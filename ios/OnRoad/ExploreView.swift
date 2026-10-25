import SwiftUI

struct Band: Codable, Hashable { let id: String; let label: String; var hint: String?; var min: Int?; var max: Int? }

/// Every active filter: several picks inside a group, all groups must match (like a shopping app).
struct Filters: Equatable {
    var band: String?
    var brands: Set<String> = []
    var bodies: Set<String> = []
    var fuels: Set<String> = []
    var gearbox: Set<String> = []
    var count: Int { (band == nil ? 0 : 1) + brands.count + bodies.count + fuels.count + gearbox.count }
}

private let carBodies = ["SUV", "Hatchback", "Sedan", "MUV", "Coupe", "Convertible", "Pickup"]
private let bikeBodies = ["Commuter", "Scooter", "Street", "Sports", "Adventure", "Cruiser", "Electric Scooter"]
private let carFuels = ["Petrol", "Diesel", "CNG", "Hybrid", "Electric"]
private let bikeFuels = ["Petrol", "Electric"]
private let bikeBands = [Band(id: "b1", label: "Under ₹1 lakh", min: nil, max: 100_000), Band(id: "b2", label: "₹1–2 lakh", min: 100_000, max: 200_000),
                         Band(id: "b3", label: "₹2–5 lakh", min: 200_000, max: 500_000), Band(id: "b4", label: "Above ₹5 lakh", min: 500_000, max: nil)]

func isAuto(_ t: String) -> Bool { !t.isEmpty && t.lowercased() != "manual" }

func matches(_ m: ModelSummary, _ f: Filters, _ bands: [Band]) -> Bool {
    if let b = f.band, let band = bands.first(where: { $0.id == b }) {
        guard let p = m.fromInr else { return false }
        if let lo = band.min, p < lo { return false }
        if let hi = band.max, p >= hi { return false }
    }
    if !f.brands.isEmpty && !f.brands.contains(m.brandSlug ?? "") { return false }
    if !f.bodies.isEmpty && !f.bodies.contains(m.bodyType ?? "") { return false }
    let fuels = (m.fuels ?? "").lowercased()
    if !f.fuels.isEmpty && !f.fuels.contains(where: { fuels.contains($0.lowercased()) }) { return false }
    let tr = (m.transmissions ?? "").split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
    if !f.gearbox.isEmpty {
        let ok = (f.gearbox.contains("Manual") && tr.contains { !isAuto($0) }) || (f.gearbox.contains("Automatic") && tr.contains { isAuto($0) })
        if !ok { return false }
    }
    return true
}

struct ExploreView: View {
    @EnvironmentObject var state: AppState
    var brandOnly: Brand? = nil
    @State private var bike = false
    @State private var all: [ModelSummary]?
    @State private var brands: [Brand] = []
    @State private var carBands: [Band] = []
    @State private var f = Filters()
    @State private var sort = "popular"
    @State private var showFilters = false
    @State private var failed = false

    var bands: [Band] { bike ? bikeBands : carBands }
    var shown: [ModelSummary]? {
        guard let all else { return nil }
        let l = all.filter { (brandOnly == nil || $0.brandSlug == brandOnly!.slug) && matches($0, f, bands) }
        switch sort {
        case "price": return l.sorted { ($0.fromInr ?? .max) < ($1.fromInr ?? .max) }
        case "price_desc": return l.sorted { ($0.fromInr ?? 0) > ($1.fromInr ?? 0) }
        case "offers": return l.sorted { ($0.offers ?? 0) > ($1.offers ?? 0) }
        default: return l
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                if brandOnly == nil {
                    Picker("", selection: $bike) { Text("Cars").tag(false); Text("Bikes & scooters").tag(true) }.pickerStyle(.segmented)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(brands) { b in
                                BrandLogo(b: b, on: f.brands.contains(b.slug)) { toggle(&f.brands, b.slug) }
                            }
                        }
                    }
                }
                if f.count > 0 {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(Array(activeChips.enumerated()), id: \.offset) { _, chip in
                                Button(action: chip.1) { Label(chip.0, systemImage: "xmark").font(.caption.weight(.semibold)) }
                                    .buttonStyle(.bordered).tint(Palette.ignition)
                            }
                            Button("Clear all") { f = Filters() }.font(.caption.bold())
                        }
                    }
                }
                Text(shown.map { "\($0.count) \(bike ? "bikes & scooters" : "cars")" } ?? "Loading…").font(.headline)
                if failed { ErrorView(message: "Couldn't reach OnRoad.") { Task { await load() } } }
                else if shown == nil { ProgressView().frame(maxWidth: .infinity).padding(30) }
                else if shown!.isEmpty {
                    VStack { Text("Nothing matches all of these in \(state.city).").foregroundStyle(Palette.mute); Button("Clear filters") { f = Filters() } }
                        .frame(maxWidth: .infinity).padding(28)
                }
                LazyVStack(spacing: 12) {
                    ForEach(shown ?? []) { m in NavigationLink(value: m) { ModelCard(m: m) }.buttonStyle(.plain) }
                }
            }.padding(16).padding(.bottom, 70)
        }
        .background(Palette.night)
        .safeAreaInset(edge: .bottom) { sortFilterBar }
        .navigationTitle(brandOnly?.name ?? "Explore")
        .navigationDestination(for: ModelSummary.self) { m in ModelView(id: m.id) }
        .sheet(isPresented: $showFilters) { FilterSheet(all: all ?? [], f: $f, bands: bands, brands: brandOnly == nil ? brands : [], bike: bike) }
        .task(id: "\(state.city)-\(bike)") { await load() }
        .onChange(of: bike) { _ in f = Filters() }
    }

    var activeChips: [(String, () -> Void)] {
        var out: [(String, () -> Void)] = []
        if let b = f.band, let band = bands.first(where: { $0.id == b }) { out.append((band.label, { f.band = nil })) }
        for s in f.brands { out.append((brands.first { $0.slug == s }?.name ?? s, { f.brands.remove(s) })) }
        for x in f.bodies { out.append((x, { f.bodies.remove(x) })) }
        for x in f.fuels { out.append((x, { f.fuels.remove(x) })) }
        for x in f.gearbox { out.append((x, { f.gearbox.remove(x) })) }
        return out
    }

    var sortFilterBar: some View {
        HStack(spacing: 0) {
            Menu {
                Picker("Sort", selection: $sort) {
                    Text("Most bought").tag("popular"); Text("Price: low to high").tag("price")
                    Text("Price: high to low").tag("price_desc"); Text("With offers").tag("offers")
                }
            } label: { Label("Sort", systemImage: "arrow.up.arrow.down").frame(maxWidth: .infinity).padding(.vertical, 14) }
            Divider().frame(height: 30)
            Button { showFilters = true } label: {
                Label(f.count > 0 ? "Filters · \(f.count)" : "Filters", systemImage: "slider.horizontal.3").frame(maxWidth: .infinity).padding(.vertical, 14)
            }
        }
        .font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ink)
        .background(Palette.panel2).clipShape(Capsule()).overlay(Capsule().stroke(Palette.line))
        .padding(.horizontal, 16).padding(.bottom, 6)
    }

    func load() async {
        failed = false; all = nil
        do {
            all = try await API.shared.get("api/explore", ["city": state.city, "type": bike ? "bike" : "car"])
            brands = ((try? await API.shared.get("api/brands", ["city": state.city, "vehicle_type": bike ? "bike" : "car"]) as [Brand]) ?? [])
                .filter { ($0.models ?? 0) > 0 }
            if carBands.isEmpty { carBands = (try? await API.shared.get("api/bands")) ?? [] }
            if let b = brandOnly { bike = all?.contains { $0.brandSlug == b.slug } == false ? !bike : bike }
        } catch { failed = true }
    }
}

func toggle(_ set: inout Set<String>, _ x: String) { if set.contains(x) { set.remove(x) } else { set.insert(x) } }

struct BrandLogo: View {
    let b: Brand
    let on: Bool
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                RemoteImage(url: b.logo ?? "/api/logos/\(b.slug)", width: 200).padding(9).frame(width: 58, height: 58)
                    .background(Color.white).clipShape(RoundedRectangle(cornerRadius: 16))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(on ? Palette.ignition : .clear, lineWidth: 2))
                Text(b.name).font(.caption2).foregroundStyle(on ? Palette.ignition : Palette.mute).lineLimit(1).frame(width: 70)
            }
        }.buttonStyle(.plain)
    }
}

/// Two-pane filter sheet with a live count of matching models.
struct FilterSheet: View {
    let all: [ModelSummary]
    @Binding var f: Filters
    let bands: [Band]
    let brands: [Brand]
    let bike: Bool
    @Environment(\.dismiss) var dismiss
    @State private var cat = "Budget"

    var cats: [String] { ["Budget"] + (brands.isEmpty ? [] : ["Brand"]) + ["Body type", "Fuel"] + (bike ? [] : ["Gearbox"]) }
    var total: Int { all.filter { matches($0, f, bands) }.count }

    var body: some View {
        NavigationStack {
            HStack(spacing: 0) {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(cats, id: \.self) { c in
                        Button { cat = c } label: {
                            Text(c).font(.subheadline.weight(cat == c ? .semibold : .regular)).foregroundStyle(cat == c ? Palette.ink : Palette.mute)
                                .frame(maxWidth: .infinity, alignment: .leading).padding(.vertical, 14).padding(.leading, 14)
                                .background(cat == c ? Palette.panel : Color.clear)
                        }.buttonStyle(.plain)
                    }
                    Spacer()
                }.frame(width: 118).background(Palette.night)
                ScrollView {
                    VStack(spacing: 10) {
                        switch cat {
                        case "Budget": ForEach(bands, id: \.id) { b in Option(title: b.label, on: f.band == b.id) { f.band = f.band == b.id ? nil : b.id } }
                        case "Brand":
                            LazyVGrid(columns: [GridItem(.adaptive(minimum: 72))], spacing: 12) {
                                ForEach(brands) { b in BrandLogo(b: b, on: f.brands.contains(b.slug)) { toggle(&f.brands, b.slug) } }
                            }
                        case "Body type": ForEach(bike ? bikeBodies : carBodies, id: \.self) { b in Option(title: b, on: f.bodies.contains(b)) { toggle(&f.bodies, b) } }
                        case "Fuel": ForEach(bike ? bikeFuels : carFuels, id: \.self) { x in Option(title: x, on: f.fuels.contains(x)) { toggle(&f.fuels, x) } }
                        default: ForEach(["Manual", "Automatic"], id: \.self) { g in Option(title: g, on: f.gearbox.contains(g)) { toggle(&f.gearbox, g) } }
                        }
                    }.padding(14)
                }.background(Palette.panel)
            }
            .safeAreaInset(edge: .bottom) {
                HStack {
                    VStack(alignment: .leading) { Text("\(total)").font(.title2.bold()); Text(bike ? "bikes & scooters" : "cars").font(.caption).foregroundStyle(Palette.mute) }
                    Spacer()
                    Button(total > 0 ? "Show results" : "No matches") { dismiss() }.buttonStyle(.borderedProminent).disabled(total == 0)
                }.padding(16).background(Palette.panel)
            }
            .navigationTitle("Filters").navigationBarTitleDisplayMode(.inline)
            .toolbar { if f.count > 0 { Button("Clear all") { f = Filters() } } }
        }
        .presentationDetents([.large])
    }
}

struct Option: View {
    let title: String
    let on: Bool
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: on ? "checkmark.square.fill" : "square").foregroundStyle(on ? Palette.ignition : Palette.mute)
                Text(title).fontWeight(.semibold).foregroundStyle(Palette.ink)
                Spacer()
            }.padding(14).background(on ? Palette.ignition.opacity(0.12) : Palette.panel2).clipShape(RoundedRectangle(cornerRadius: 14))
        }.buttonStyle(.plain)
    }
}
