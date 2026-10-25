import SwiftUI

struct ModelView: View {
    let id: String
    @EnvironmentObject var state: AppState
    @State private var m: ModelDetail?
    @State private var failed = false
    @State private var sel: String?
    @State private var tab = "price"
    @State private var specs: VariantSpecs?
    @State private var quoting = false

    var variant: Variant? { m?.variants.first { $0.id == sel } ?? m?.variants.first { $0.exShowroomInr != nil } ?? m?.variants.first }

    var body: some View {
        ScrollView {
            if let m {
                VStack(alignment: .leading, spacing: 16) {
                    GalleryView(items: (m.gallery?.isEmpty == false ? m.gallery! : [GalleryItem(url: m.imageUrl ?? "", label: m.name, kind: "model")]))
                    VStack(alignment: .leading, spacing: 4) {
                        Text(m.brandName ?? "").foregroundStyle(Palette.mute)
                        Text(m.name).font(.largeTitle.bold())
                        let prices = m.variants.compactMap { $0.exShowroomInr }
                        Text(range(prices.min(), prices.max())).font(.title3.bold()).foregroundStyle(Palette.ignition)
                        Text(priceLabel(variant?.priceCity, state.city) + " · \(m.variants.count) variants").font(.caption).foregroundStyle(Palette.mute)
                    }.padding(.horizontal, 16)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(m.variants) { v in
                                Button { sel = v.id } label: {
                                    VStack(alignment: .leading, spacing: 3) {
                                        Text(v.name).font(.subheadline.weight(.semibold)).lineLimit(1)
                                        Text([v.fuel, v.transmission].compactMap { $0 }.joined(separator: " · ")).font(.caption).foregroundStyle(Palette.mute)
                                        Text(rupees(v.exShowroomInr)).font(.subheadline.bold())
                                    }.frame(width: 160, alignment: .leading).padding(12)
                                    .background(v.id == variant?.id ? Palette.ignition.opacity(0.16) : Palette.panel)
                                    .clipShape(RoundedRectangle(cornerRadius: 16))
                                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(v.id == variant?.id ? Palette.ignition : Palette.line))
                                }.buttonStyle(.plain)
                            }
                        }.padding(.horizontal, 16)
                    }

                    KeySpecs(specs: specs)

                    Picker("", selection: $tab) {
                        Text("Price").tag("price"); Text("Specs").tag("specs"); Text("Safety").tag("safety"); Text("Showrooms").tag("dealers")
                        if m.offers?.isEmpty == false { Text("Offers").tag("offers") }
                    }.pickerStyle(.segmented).padding(.horizontal, 16)

                    Group {
                        switch tab {
                        case "specs": SpecsList(specs: specs)
                        case "safety": SafetyList(tests: m.crashTests ?? [], name: m.name)
                        case "dealers": DealersList(dealers: m.dealers, city: state.city)
                        case "offers": ForEach(m.offers ?? [], id: \.self) { o in
                            Card { VStack(alignment: .leading, spacing: 4) {
                                Text(o.title).font(.headline)
                                if let a = o.amountInr { Text(rupees(a)).font(.title3.bold()).foregroundStyle(Palette.good) }
                                if let v = o.validUntil { Text("Valid until \(v)").font(.caption).foregroundStyle(Palette.mute) }
                            } }
                        }
                        default: PriceBreakup(v: variant)
                        }
                    }.padding(.horizontal, 16)
                }.padding(.bottom, 30)
            } else if failed {
                ErrorView(message: "Couldn't load this car. Check your connection.") { Task { await load() } }
            } else {
                ProgressView().padding(60)
            }
        }
        .background(Palette.night)
        .safeAreaInset(edge: .bottom) {
            // pinned: this variant's on-road price and the main action
            if m != nil {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("On-road · \(variant?.name ?? "")").font(.caption).foregroundStyle(Palette.mute).lineLimit(1)
                        Text(rupees(variant?.onroad.map { $0.totalInr - $0.refundableInr } ?? variant?.exShowroomInr)).font(.title3.bold())
                    }
                    Spacer()
                    Button { quoting = true } label: { Text("Get best price").fontWeight(.semibold).padding(.horizontal, 10).padding(.vertical, 6) }
                        .buttonStyle(.borderedProminent)
                }.padding(.horizontal, 16).padding(.vertical, 10).background(Palette.panel)
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .task(id: state.city) { await load() }
        .task(id: variant?.id) { specs = nil; if let v = variant { specs = try? await API.shared.get("api/variant-specs", ["variant_id": v.id]) } }
        .sheet(isPresented: $quoting) { if let v = variant { QuoteSheet(variant: v) } }
    }

    func load() async {
        failed = false
        let parts = id.split(separator: "/", maxSplits: 1).map(String.init)
        guard parts.count == 2 else { failed = true; return }
        var q: [String: String?] = ["city": state.city]
        if let c = state.coord { q["lat"] = String(c.latitude); q["lng"] = String(c.longitude) }
        do { m = try await API.shared.get("api/models/\(parts[0])/\(parts[1])", q) } catch { failed = true }
    }
}

/// Engine, power, torque, mileage / range and seats at a glance, from the variant's official sheet.
struct KeySpecs: View {
    let specs: VariantSpecs?
    static let wanted: [(String, String)] = [("Engine", "displacement|engine capacity|cubic"), ("Power", "max(imum)? ?power|^power"),
        ("Torque", "torque"), ("Mileage", "mileage|fuel efficiency"), ("Range", "\\brange\\b"), ("Seats", "seating")]
    var body: some View {
        let rows = specs?.specs ?? []
        let glance: [(String, String)] = Self.wanted.compactMap { label, rx in
            rows.first { $0.label.range(of: rx, options: [.regularExpression, .caseInsensitive]) != nil }.map { (label, $0.value) }
        }
        if !glance.isEmpty {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(glance.indices, id: \.self) { i in
                        let item = glance[i]
                        VStack(alignment: .leading, spacing: 3) {
                            Text(item.0.uppercased()).font(.caption2.weight(.semibold)).foregroundStyle(Palette.mute)
                            Text(item.1).font(.subheadline.weight(.semibold)).lineLimit(2)
                        }.frame(width: 120, alignment: .leading).padding(12).background(Palette.panel)
                            .clipShape(RoundedRectangle(cornerRadius: 16)).overlay(RoundedRectangle(cornerRadius: 16).stroke(Palette.line))
                    }
                }.padding(.horizontal, 16)
            }
        }
    }
}

struct GalleryView: View {
    let items: [GalleryItem]
    @State private var page = 0
    var body: some View {
        VStack(spacing: 6) {
            TabView(selection: $page) {
                ForEach(Array(items.enumerated()), id: \.offset) { i, it in
                    RemoteImage(url: it.url, width: 1200).tag(i).padding(.horizontal, 8)
                }
            }.tabViewStyle(.page(indexDisplayMode: .never)).frame(height: 240)
            if items.count > 1 {
                Text("\(page + 1) / \(items.count)\(items[safe: page]?.label.map { " · \($0)" } ?? "")").font(.caption).foregroundStyle(Palette.mute)
            }
        }
    }
}

extension Array {
    subscript(safe i: Int) -> Element? { indices.contains(i) ? self[i] : nil }
}

struct PriceBreakup: View {
    let v: Variant?
    var body: some View {
        Card {
            if let b = v?.onroad {
                VStack(alignment: .leading, spacing: 10) {
                    Text("ON-ROAD IN \((b.stateName ?? "").uppercased())").font(.caption).foregroundStyle(Palette.mute)
                    Text(rupees(b.totalInr - b.refundableInr)).font(.largeTitle.bold())
                    if b.refundableInr > 0 { Text("+ \(rupees(b.refundableInr)) TCS, refunded in your tax return").font(.caption).foregroundStyle(Palette.mute) }
                    ForEach(b.lines.filter { $0.refundable != true }, id: \.self) { l in
                        HStack(alignment: .top) {
                            VStack(alignment: .leading) { Text(l.label).font(.subheadline.weight(.semibold)); Text(l.basis ?? "").font(.caption).foregroundStyle(Palette.mute) }
                            Spacer(); Text(rupees(l.amountInr)).fontWeight(.semibold)
                        }
                    }
                    EmiRow(total: b.totalInr - b.refundableInr)
                }
            } else {
                Text("This variant has no published price.").foregroundStyle(Palette.mute)
            }
        }
    }
}

/// EMI at a typical car-loan rate; the buyer moves the down payment, tenure and rate.
struct EmiRow: View {
    let total: Int
    @State private var down = 0.2
    @State private var years = 5.0
    @State private var rate = 9.0
    var emi: Int {
        let p = Double(total) * (1 - down), r = rate / 1200, n = years * 12
        return Int((p * r * pow(1 + r, n) / (pow(1 + r, n) - 1)).rounded())
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Divider().overlay(Palette.line)
            HStack {
                Text("EMI \(rupees(emi)) / month").font(.title3.bold()).foregroundStyle(Palette.electric)
                Spacer()
                Art(name: "hero-emi", height: 56)
            }
            Text("\(Int(down * 100))% down · \(Int(years)) years · \(String(format: "%.1f", rate))%").font(.caption).foregroundStyle(Palette.mute)
            Slider(value: $down, in: 0...0.8, step: 0.05)
            Slider(value: $years, in: 1...8, step: 1)
            Slider(value: $rate, in: 7...14, step: 0.25)
        }
    }
}

struct SpecsList: View {
    let specs: VariantSpecs?
    var body: some View {
        if let s = specs {
            VStack(alignment: .leading, spacing: 12) {
                let groups = Dictionary(grouping: s.specs, by: { $0.grp ?? "Specifications" })
                ForEach(groups.keys.sorted(), id: \.self) { g in
                    Card { VStack(alignment: .leading, spacing: 8) {
                        Text(g).font(.headline)
                        ForEach(groups[g] ?? [], id: \.self) { r in
                            HStack(alignment: .top) { Text(r.label).foregroundStyle(Palette.mute); Spacer(); Text(r.value).multilineTextAlignment(.trailing) }.font(.subheadline)
                        }
                    } }
                }
                if !s.features.isEmpty {
                    Card { VStack(alignment: .leading, spacing: 6) {
                        Text("Features").font(.headline)
                        ForEach(s.features.filter { $0.key != "other" }, id: \.self) { f in
                            Label(f.label, systemImage: "checkmark.circle.fill").font(.subheadline).foregroundStyle(Palette.ink)
                        }
                    } }
                }
                if s.specs.isEmpty && s.features.isEmpty { Text("The maker hasn't published a spec sheet we can read yet.").foregroundStyle(Palette.mute) }
            }
        } else { ProgressView().frame(maxWidth: .infinity).padding(20) }
    }
}

struct SafetyList: View {
    let tests: [CrashTest]
    let name: String
    @Environment(\.openURL) var openURL
    var body: some View {
        if tests.isEmpty { Text("No official Bharat NCAP or Global NCAP result on record for the \(name).").foregroundStyle(Palette.mute) }
        ForEach(tests, id: \.self) { t in
            Button { if let u = t.sourceUrl.flatMap(URL.init) { openURL(u) } } label: {
                Card { VStack(alignment: .leading, spacing: 6) {
                    Label(t.agency ?? "NCAP", systemImage: "shield.lefthalf.filled").foregroundStyle(Palette.good).font(.headline)
                    Text("Adult \(t.adultStars.map(String.init) ?? "—")★   Child \(t.childStars.map(String.init) ?? "—")★").font(.title3.bold())
                    Text("Tap for the official result").font(.caption).foregroundStyle(Palette.electric)
                } }
            }.buttonStyle(.plain)
        }
    }
}

struct DealersList: View {
    let dealers: [Dealer]
    let city: String
    var body: some View {
        if dealers.isEmpty { Text("No showroom listed for \(city).").foregroundStyle(Palette.mute) }
        ForEach(dealers) { d in DealerCard(d: d) }
    }
}

struct QuoteIn: Encodable { let variantId: String; let city: String; var note: String?; var consent = true }
struct QuoteSheet: View {
    let variant: Variant
    @EnvironmentObject var state: AppState
    @Environment(\.dismiss) var dismiss
    @State private var note = ""
    @State private var msg: String?
    @State private var busy = false
    var body: some View {
        NavigationStack {
            Form {
                Section { Art(name: msg == nil ? "hero-quote" : "success-quote-sent", height: 130).frame(maxWidth: .infinity) }.listRowBackground(Color.clear)
                Section { Text(variant.name).font(.headline); Text("Dealers in \(state.city) send you their best on-road price.").foregroundStyle(Palette.mute) }
                Section("Anything dealers should know?") { TextField("Colour, exchange, finance…", text: $note, axis: .vertical) }
                Section { Text("Your name and contact go only to the official showrooms near you that answer this request.").font(.caption).foregroundStyle(Palette.mute) }
                if let msg { Text(msg).foregroundStyle(Palette.ignition) }
                Button(busy ? "Sending…" : "Ask for quotes") {
                    guard state.account != nil else { msg = "Sign in from the Profile tab first."; return }
                    busy = true
                    Task {
                        do { let _: OK = try await API.shared.post("api/quotes/request", QuoteIn(variantId: variant.id, city: state.city, note: note)); dismiss() }
                        catch { msg = error.localizedDescription }
                        busy = false
                    }
                }.disabled(busy)
            }.navigationTitle("Dealer quotes")
        }
    }
}

/// Where the ex-showroom figure comes from, said plainly when the maker doesn't list the chosen city.
func priceLabel(_ pc: String?, _ city: String) -> String {
    guard let pc, pc.lowercased() != city.lowercased() else { return "Ex-showroom price in \(city)" }
    return pc == "India (national)" ? "Ex-showroom · same price across India" : "Ex-showroom · \(city) (nearest listed price, \(pc))"
}
