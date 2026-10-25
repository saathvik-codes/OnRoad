import SwiftUI

struct HomeView: View {
    @EnvironmentObject var state: AppState
    @State private var popular: [ModelSummary] = []
    @State private var offers: [Offer] = []
    @State private var failed = false
    @State private var picking = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("OnRoad").font(.largeTitle.bold())
                        Button { picking = true } label: {
                            Label(state.city, systemImage: "mappin.circle.fill").font(.subheadline.weight(.semibold))
                        }.tint(Palette.electric)
                    }
                    Spacer()
                    NavigationLink { SearchView() } label: {
                        Image(systemName: "magnifyingglass").font(.title3).padding(12).background(Palette.panel2).clipShape(Circle())
                    }.tint(Palette.ink)
                }
                Text("Official prices, the full on-road bill and real dealer quotes for \(state.city).").foregroundStyle(Palette.mute)

                HStack(spacing: 12) {
                    NavigationLink { FinderView() } label: { QuickAction(icon: "sparkles", title: "Find my car") }
                    NavigationLink { ShowroomsView() } label: { QuickAction(icon: "mappin.and.ellipse", title: "Showrooms") }
                    NavigationLink { OffersView() } label: { QuickAction(icon: "tag", title: "Offers") }
                }.buttonStyle(.plain)

                if !offers.isEmpty {
                    Text("Offers this month").font(.title3.bold())
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(offers.prefix(8)) { o in OfferTile(o: o).frame(width: 280) }
                        }
                    }
                }

                Text("Most bought in India").font(.title3.bold())
                if failed { ErrorView(message: "Couldn't reach OnRoad. Check your connection.") { Task { await load() } } }
                else if popular.isEmpty { ProgressView().frame(maxWidth: .infinity).padding(30) }
                LazyVStack(spacing: 12) {
                    ForEach(popular.prefix(12)) { m in
                        NavigationLink(value: m) { ModelCard(m: m) }.buttonStyle(.plain)
                    }
                }
            }.padding(16)
        }
        .background(Palette.night)
        .navigationDestination(for: ModelSummary.self) { m in ModelView(id: m.id) }
        .sheet(isPresented: $picking) { CityPicker() }
        .task(id: state.city) { await load() }
        .refreshable { await load() }
    }

    func load() async {
        failed = false
        do {
            async let p: [ModelSummary] = API.shared.get("api/explore", ["city": state.city, "type": "car"])
            async let o: [Offer] = API.shared.get("api/offers", ["city": state.city, "limit": "20"])
            popular = try await p
            offers = (try? await o) ?? []
        } catch { failed = true }
    }
}

struct QuickAction: View {
    let icon: String
    let title: String
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon).font(.title2).foregroundStyle(Palette.ignition)
            Text(title).font(.caption.weight(.semibold)).foregroundStyle(Palette.ink)
        }.frame(maxWidth: .infinity).padding(.vertical, 16).background(Palette.panel)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

struct ModelCard: View {
    let m: ModelSummary
    var body: some View {
        Card {
            HStack(spacing: 14) {
                RemoteImage(url: m.imageUrl, width: 480).frame(width: 128, height: 80)
                VStack(alignment: .leading, spacing: 4) {
                    Text(m.brand ?? "").font(.caption).foregroundStyle(Palette.mute)
                    Text(m.name).font(.headline).lineLimit(1)
                    Text(range(m.fromInr, m.toInr)).font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ignition)
                    HStack(spacing: 6) {
                        if let r = m.salesRank, r <= 25 { Chip(text: "#\(r) seller", color: Palette.good) }
                        if let o = m.offers, o > 0 { Chip(text: "Offers", color: Palette.amber) }
                        if let b = m.bodyType { Chip(text: b) }
                    }
                }
                Spacer(minLength: 0)
            }
        }
    }
}

struct OfferTile: View {
    let o: Offer
    var body: some View {
        Card {
            HStack(spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 14).fill(Color(hex: 0xF3F4F7))
                    RemoteImage(url: o.modelImage ?? "/api/logos/\(o.brandSlug ?? "")", width: 400).padding(6)
                }.frame(width: 96, height: 68)
                VStack(alignment: .leading, spacing: 3) {
                    Text([o.brandName, o.modelName].compactMap { $0 }.joined(separator: " ")).font(.subheadline.bold()).lineLimit(1)
                    if let a = o.amountInr { Text("Benefits up to \(rupees(a))").font(.caption.weight(.semibold)).foregroundStyle(Palette.good) }
                    Text(o.title).font(.caption).foregroundStyle(Palette.mute).lineLimit(2)
                }
            }
        }
    }
}

struct CityPicker: View {
    @EnvironmentObject var state: AppState
    @Environment(\.dismiss) var dismiss
    @State private var cities: [City] = []
    @State private var q = ""
    var body: some View {
        NavigationStack {
            List {
                Button { state.locate(); dismiss() } label: { Label("Use my location", systemImage: "location.fill") }
                ForEach(cities.filter { q.isEmpty || $0.name.localizedCaseInsensitiveContains(q) }) { c in
                    Button { state.choose(c); dismiss() } label: {
                        HStack { Text(c.name); Spacer(); Text(c.stateName ?? "").foregroundStyle(Palette.mute) }
                    }
                }
            }
            .searchable(text: $q, prompt: "Search city")
            .navigationTitle("Your city")
            .task { cities = (try? await API.shared.get("api/cities")) ?? [] }
        }
    }
}

struct SearchView: View {
    @State private var q = ""
    @State private var hits: [Hit] = []
    var body: some View {
        List(hits) { h in
            NavigationLink { ModelView(id: h.id) } label: {
                VStack(alignment: .leading) {
                    Text("\(h.brand ?? "") \(h.name)").font(.headline)
                    if let n = h.note { Text(n).font(.caption).foregroundStyle(Palette.ignition) }
                    Text(rupees(h.fromInr)).font(.caption).foregroundStyle(Palette.mute)
                }
            }
        }
        .searchable(text: $q, placement: .navigationBarDrawer(displayMode: .always), prompt: "Creta, Nexon, Thar…")
        .navigationTitle("Search")
        .task(id: q) {
            try? await Task.sleep(nanoseconds: 250_000_000)
            hits = q.count < 2 ? [] : ((try? await API.shared.get("api/search", ["q": q])) ?? [])
        }
    }
}
