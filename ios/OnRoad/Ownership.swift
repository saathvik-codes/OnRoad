import SwiftUI
import FirebaseAnalytics

// MARK: - Data

struct OwnLine: Codable, Hashable { var label: String; var amountInr: Int?; var basis: String? }
struct OwnLink: Codable, Hashable { var name: String?; var title: String?; var url: String }
struct OwnRule: Codable, Hashable { var item: String; var status: String? }
struct Insurer: Codable, Hashable { var name: String; var url: String; var logoUrl: String?; var logoDark: Bool?; var garages: String? }
struct OwnInsurance: Codable { var lines: [OwnLine]; var tips: [String]; var insurers: [Insurer]; var compare: [OwnLink]; var disclosure: String }
struct OwnEv: Codable { var lifeTaxExempt: Bool?; var validTo: String? }
struct OwnRta: Codable { var state: String; var charges: [OwnLine]; var steps: [String]; var notAllowed: [OwnRule]; var sources: [OwnLink]; var links: [OwnLink]; var ev: OwnEv? }
struct Accessory: Codable, Hashable, Identifiable { var code: String; var name: String; var category: String?; var priceInr: Int?; var imageUrl: String?; var id: String { code } }
struct OwnAccessoryLink: Codable { var url: String }
struct OwnAccessories: Codable { var items: [Accessory]?; var official: OwnAccessoryLink?; var advice: [String] }
struct UpdateItem: Codable, Hashable { var kind: String; var date: String; var modelId: String?; var title: String; var detail: String?; var imageUrl: String? }
struct Ownership: Codable { var insurance: OwnInsurance; var rta: OwnRta; var accessories: OwnAccessories; var updates: [UpdateItem] }
struct NewsItem: Codable, Hashable, Identifiable {
    var id: String; var title: String; var summary: String?; var url: String; var imageUrl: String?; var source: String
    var published: String; var modelId: String?; var modelName: String?; var topic: String
}

let topicName = ["launch": "Launch", "price": "Price", "safety": "Safety", "ev": "Electric", "policy": "Rules & tax",
                 "sales": "Sales", "spied": "Spotted testing", "industry": "Industry"]

func ago(_ iso: String) -> String {
    let f = ISO8601DateFormatter()
    guard let d = f.date(from: iso) else { return "" }
    let h = max(1, Int(Date().timeIntervalSince(d) / 3600))
    return h < 24 ? "\(h)h ago" : "\(h / 24)d ago"
}

/// Firebase Analytics with Google's recommended event names; ids only, never personal data.
enum Track {
    static func viewCar(_ id: String, brand: String, city: String) { Analytics.logEvent(AnalyticsEventViewItem, parameters: [AnalyticsParameterItemID: id, AnalyticsParameterItemBrand: brand, "city": city]) }
    static func pickVariant(_ id: String) { Analytics.logEvent(AnalyticsEventSelectItem, parameters: [AnalyticsParameterItemID: id]) }
    static func quote(_ id: String, city: String) { Analytics.logEvent(AnalyticsEventGenerateLead, parameters: [AnalyticsParameterItemID: id, "city": city]) }
    static func search(_ q: String) { Analytics.logEvent(AnalyticsEventSearch, parameters: [AnalyticsParameterSearchTerm: String(q.prefix(80))]) }
    static func news(_ source: String, _ topic: String) { Analytics.logEvent(AnalyticsEventSelectContent, parameters: [AnalyticsParameterContentType: "news", "source": source, "topic": topic]) }
}

// MARK: - Variant picker

struct VariantCard: View {
    let v: Variant?; let count: Int; let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("VARIANT").font(.caption2.weight(.semibold)).foregroundStyle(Palette.mute)
                    Text(v?.name ?? "Choose a variant").font(.headline).lineLimit(1)
                    Text([v?.fuel, v?.transmission].compactMap { $0 }.joined(separator: " · ")).font(.caption).foregroundStyle(Palette.mute)
                }
                Spacer()
                Text("Change (\(count))").font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ignition)
            }.padding(14).background(Palette.panel).clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(Palette.line))
        }.buttonStyle(.plain).padding(.horizontal, 16)
    }
}

struct VariantPickerSheet: View {
    let variants: [Variant]; let selected: String?; let pick: (String) -> Void
    @Environment(\.dismiss) var dismiss
    @State private var fuel: String?
    @State private var gear: String?
    @State private var q = ""
    var body: some View {
        let fuels = Array(Set(variants.compactMap { $0.fuel })).sorted()
        let isAuto = { (v: Variant) in (v.transmission ?? "").lowercased() != "manual" }
        let shown = variants.filter { v in
            (fuel == nil || v.fuel == fuel) && (gear == nil || (gear == "Automatic") == isAuto(v)) &&
                (q.isEmpty || v.name.localizedCaseInsensitiveContains(q))
        }.sorted { ($0.exShowroomInr ?? Int.max) < ($1.exShowroomInr ?? Int.max) }
        NavigationStack {
            List {
                if fuels.count > 1 || variants.contains(where: isAuto) {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            if fuels.count > 1 { ForEach([nil] + fuels.map { Optional($0) }, id: \.self) { f in Pill(text: f ?? "All fuels", on: fuel == f) { fuel = f } } }
                            ForEach([nil, "Manual", "Automatic"], id: \.self) { g in Pill(text: g ?? "Any gearbox", on: gear == g) { gear = g } }
                        }
                    }.listRowSeparator(.hidden)
                }
                ForEach(shown) { v in
                    Button { pick(v.id); dismiss() } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(v.name).font(.subheadline.weight(.semibold)).foregroundStyle(v.id == selected ? Palette.ignition : Palette.ink)
                                Text([v.fuel, v.transmission].compactMap { $0 }.joined(separator: " · ")).font(.caption).foregroundStyle(Palette.mute)
                            }
                            Spacer()
                            VStack(alignment: .trailing) {
                                Text(rupees(v.exShowroomInr)).font(.subheadline.bold())
                                if let o = v.onroad { Text("on-road \(rupees(o.totalInr - o.refundableInr))").font(.caption).foregroundStyle(Palette.mute) }
                            }
                        }
                    }
                }
            }
            .searchable(text: $q, prompt: "Search, e.g. ZXi, AMT")
            .navigationTitle("Choose a variant").navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - Insurance & RTA

struct OwnershipView: View {
    let variantId: String?; let brand: String
    @EnvironmentObject var state: AppState
    @State private var o: Ownership?
    @State private var failed = false
    @State private var part = "insurance"
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Picker("", selection: $part) {
                Text("Insurance").tag("insurance"); Text("Registration").tag("rta"); Text("Accessories").tag("acc")
            }.pickerStyle(.segmented)
            if let o {
                switch part {
                case "rta":
                    Text("Registration in \(o.rta.state)").font(.headline)
                    Amounts(lines: o.rta.charges)
                    if o.rta.ev?.lifeTaxExempt == true { Text("Electric vehicles pay no road tax in \(o.rta.state).").foregroundStyle(Palette.good) }
                    Text("How it works").font(.headline)
                    ForEach(Array(o.rta.steps.enumerated()), id: \.offset) { i, s in Text("\(i + 1). \(s)").font(.caption).foregroundStyle(Palette.mute) }
                    Text("Charges a dealer cannot add").font(.headline)
                    ForEach(o.rta.notAllowed, id: \.self) { r in Text("• \(r.item): \(r.status ?? "")").font(.caption).foregroundStyle(Palette.mute) }
                    ForEach(o.rta.links + o.rta.sources, id: \.self) { l in Link((l.title ?? l.name ?? "") + " ↗", destination: URL(string: l.url)!).font(.subheadline) }
                case "acc":
                    let items = o.accessories.items ?? []
                    if !items.isEmpty {
                        Text("\(items.count) genuine accessories at \(brand)'s list prices").font(.caption).foregroundStyle(Palette.mute)
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                            ForEach(items) { a in
                                VStack(alignment: .leading, spacing: 4) {
                                    AsyncImage(url: URL(string: a.imageUrl ?? "")) { $0.resizable().scaledToFill() } placeholder: { Color.white }
                                        .frame(height: 100).frame(maxWidth: .infinity).clipped().background(Color.white)
                                    Text(a.name).font(.caption.weight(.semibold)).lineLimit(2)
                                    if let p = a.priceInr { Text(rupees(p)).font(.caption.bold()) }
                                }.padding(8).background(Palette.panel).clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                        }
                    } else if let u = o.accessories.official { Link("\(brand) accessories store ↗", destination: URL(string: u.url)!) }
                    else { Text("\(brand) doesn't publish an accessory catalogue online. Ask the dealer for the itemised price list.").foregroundStyle(Palette.mute) }
                    ForEach(o.accessories.advice, id: \.self) { Text("• \($0)").font(.caption).foregroundStyle(Palette.mute) }
                default:
                    Amounts(lines: o.insurance.lines)
                    ForEach(o.insurance.tips, id: \.self) { Text("• \($0)").font(.caption).foregroundStyle(Palette.mute) }
                    Text("Get your own quotes").font(.headline)
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                        ForEach(o.insurance.insurers, id: \.self) { i in
                            Link(destination: URL(string: i.url)!) {
                                VStack(alignment: .leading, spacing: 4) {
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 10).fill(i.logoDark == true ? Color(hex: 0x1B1F2A) : .white)
                                        if let l = i.logoUrl { RemoteImage(url: l, width: 300).padding(6) } else { Text(i.name).font(.headline).foregroundStyle(Color(hex: 0x1B1F2A)) }
                                    }.frame(height: 44)
                                    Text(i.name).font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ink)
                                    Text(i.garages.map { "\($0) cashless garages*" } ?? "Get a quote").font(.caption).foregroundStyle(Palette.mute)
                                }.padding(10).background(Palette.panel).clipShape(RoundedRectangle(cornerRadius: 14))
                            }
                        }
                    }
                    Text("* As stated on each insurer's website. " + o.insurance.disclosure).font(.caption2).foregroundStyle(Palette.mute)
                }
            } else if failed { Text("Couldn't load this right now.").foregroundStyle(Palette.mute) }
            else { ProgressView().frame(maxWidth: .infinity) }
        }
        .task(id: (variantId ?? "") + state.city) {
            guard let v = variantId else { return }
            o = nil; failed = false
            do { o = try await API.shared.get("api/ownership", ["variant_id": v, "city": state.city]) } catch { failed = true }
        }
    }
}

struct Amounts: View {
    let lines: [OwnLine]
    var body: some View {
        VStack(spacing: 0) {
            ForEach(lines, id: \.self) { l in
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(l.label).font(.subheadline.weight(.semibold))
                        if let b = l.basis { Text(b).font(.caption).foregroundStyle(Palette.mute).lineLimit(3) }
                    }
                    Spacer()
                    Text(l.amountInr.map { rupees($0) } ?? "—").font(.subheadline.bold())
                }.padding(12)
                Divider().overlay(Palette.line)
            }
        }.background(Palette.panel).clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

// MARK: - News

struct NewsCarousel: View {
    let news: [NewsItem]
    @State private var page = 0
    private let timer = Timer.publish(every: 6, on: .main, in: .common).autoconnect()
    var body: some View {
        let slides = Array(news.filter { $0.imageUrl != nil }.prefix(6))
        if !slides.isEmpty {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("What's new").font(.title3.bold())
                    Spacer()
                    NavigationLink("All updates") { UpdatesView() }.font(.subheadline.weight(.semibold)).tint(Palette.ignition)
                }
                TabView(selection: $page) {
                    ForEach(Array(slides.enumerated()), id: \.offset) { i, n in
                        Link(destination: URL(string: n.url)!) {
                            ZStack(alignment: .bottomLeading) {
                                AsyncImage(url: URL(string: n.imageUrl ?? "")) { img in img.resizable().scaledToFill() } placeholder: { Palette.panel2 }
                                LinearGradient(colors: [.clear, .black.opacity(0.8)], startPoint: .top, endPoint: .bottom)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("\(topicName[n.topic] ?? "News") · \(n.source) · \(ago(n.published))".uppercased())
                                        .font(.caption2.weight(.semibold)).foregroundStyle(.white.opacity(0.85))
                                    Text(n.title).font(.headline).foregroundStyle(.white).lineLimit(3)
                                }.padding(14)
                            }.clipShape(RoundedRectangle(cornerRadius: 20))
                        }.simultaneousGesture(TapGesture().onEnded { Track.news(n.source, n.topic) }).tag(i)
                    }
                }.tabViewStyle(.page(indexDisplayMode: .always)).frame(height: 220)
                .onReceive(timer) { _ in withAnimation { page = (page + 1) % max(1, slides.count) } }
            }
        }
    }
}

struct UpdatesView: View {
    @AppStorage("updates.tab") private var tab = "news"
    @AppStorage("updates.topic") private var topic = ""          // "" = all topics
    @AppStorage("updates.kind") private var kind = ""            // "" = everything
    @State private var news: [NewsItem]? = nil
    @State private var ups: [UpdateItem]? = nil

    private var topics: [(String, String)] { [("", "All")] + ["launch", "price", "safety", "ev", "policy", "sales", "spied"].map { ($0, topicName[$0] ?? $0) } }
    private var kinds: [(String, String, Int?)] {
        let l = ups ?? []
        let all: [(String, String, Int?)] = [("", "All", l.count), ("new", "Launches", l.filter { $0.kind == "new" }.count),
                                            ("price", "Price changes", l.filter { $0.kind == "price" }.count), ("offer", "Offers", l.filter { $0.kind == "offer" }.count)]
        return ups == nil ? all.map { ($0.0, $0.1, nil) } : all.filter { $0.0.isEmpty || ($0.2 ?? 0) > 0 || $0.0 == kind }
    }

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 0, pinnedViews: [.sectionHeaders]) {
                Picker("", selection: $tab) { Text("News").tag("news"); Text("Prices & launches").tag("prices") }
                    .pickerStyle(.segmented).padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 4)
                Section {
                    if tab == "news" { newsList } else { updatesList }
                } header: {
                    // filters stay pinned while the list scrolls
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            if tab == "news" {
                                ForEach(topics, id: \.0) { t in UpdChip(label: t.1, count: nil, on: topic == t.0) { topic = t.0 } }
                            } else {
                                ForEach(kinds, id: \.0) { k in UpdChip(label: k.1, count: k.2, on: kind == k.0) { kind = k.0 } }
                            }
                        }.padding(.horizontal, 16).padding(.vertical, 10)
                    }.background(Palette.night)
                }
            }.padding(.bottom, 24)
        }
        .background(Palette.night)
        .navigationTitle("Updates")
        .task(id: topic) { news = nil; news = (try? await API.shared.get("api/news", ["limit": "60", "topic": topic.isEmpty ? nil : topic])) ?? [] }
        .task { ups = (try? await API.shared.get("api/updates", ["vehicle_type": "car", "limit": "80"])) ?? [] }
    }

    @ViewBuilder private var newsList: some View {
        if let list = news {
            if list.isEmpty { UpdEmpty(title: "No stories in this topic yet.", sub: "Try All, or check back later today.") }
            ForEach(list) { n in
                Link(destination: URL(string: n.url)!) {
                    HStack(alignment: .top, spacing: 12) {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack(spacing: 8) {
                                UpdTag(text: topicName[n.topic] ?? "News", color: Palette.ignition)
                                Text("\(n.source) · \(ago(n.published))").font(.caption2).foregroundStyle(Palette.mute).lineLimit(1)
                            }
                            Text(n.title).font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ink).lineLimit(3).multilineTextAlignment(.leading)
                        }
                        Spacer(minLength: 0)
                        if let u = n.imageUrl { AsyncImage(url: URL(string: u)) { $0.resizable().scaledToFill() } placeholder: { Palette.panel2 }
                            .frame(width: 96, height: 72).clipShape(RoundedRectangle(cornerRadius: 12)) }
                    }.padding(.horizontal, 16).padding(.vertical, 12)
                }.simultaneousGesture(TapGesture().onEnded { Track.news(n.source, n.topic) })
                Divider().overlay(Palette.line).padding(.leading, 16)
            }
        } else { ForEach(0..<5, id: \.self) { _ in UpdSkeleton() } }
    }

    @ViewBuilder private var updatesList: some View {
        if let all = ups {
            let list = all.filter { kind.isEmpty || $0.kind == kind }
            if list.isEmpty {
                UpdEmpty(title: kind == "new" ? "No new models in the last four months." : kind == "price" ? "No lasting price changes in the last four months."
                         : kind == "offer" ? "No current manufacturer offers." : "Nothing new in the last four months.",
                         sub: "Makers' own websites are checked every few hours.")
            }
            ForEach(list, id: \.self) { u in
                if let id = u.modelId { NavigationLink { ModelView(id: id) } label: { UpdCard(u: u) }.buttonStyle(.plain) } else { UpdCard(u: u) }
            }
        } else { ForEach(0..<5, id: \.self) { _ in UpdSkeleton() } }
    }
}

/// Filter chip: the chosen one is tinted with the brand colour; optional count.
private struct UpdChip: View {
    let label: String; let count: Int?; let on: Bool; let tap: () -> Void
    var body: some View {
        Button(action: tap) {
            HStack(spacing: 6) {
                Text(label).font(.subheadline.weight(on ? .semibold : .medium)).foregroundStyle(on ? Palette.ignition : Palette.ink)
                if let c = count { Text("\(c)").font(.caption.weight(.medium)).foregroundStyle(on ? Palette.ignition : Palette.mute) }
            }
            .padding(.horizontal, 14).frame(height: 36)
            .background(on ? Palette.ignition.opacity(0.12) : Palette.panel, in: Capsule())
            .overlay(Capsule().stroke(on ? Palette.ignition : Palette.line, lineWidth: 1))
        }.buttonStyle(.plain)
    }
}

private struct UpdTag: View {
    let text: String; let color: Color
    var body: some View {
        Text(text).font(.caption2.weight(.semibold)).foregroundStyle(color)
            .padding(.horizontal, 7).padding(.vertical, 2).background(color.opacity(0.12), in: RoundedRectangle(cornerRadius: 6))
    }
}

private struct UpdCard: View {
    let u: UpdateItem
    private var tag: (String, Color) {
        switch u.kind {
        case "new": return ("New launch", Palette.ignition)
        case "offer": return ("Offer", Palette.good)
        case "price":
            let t = (u.title + " " + (u.detail ?? "")).lowercased()
            return ["cut", "lower", "drop", "reduc"].contains(where: { t.contains($0) }) ? ("Price cut", Palette.good) : ("Price rise", Palette.amber)
        default: return ("Update", Palette.mute)
        }
    }
    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Palette.panel2
                if let s = u.imageUrl, let url = URL(string: s) { AsyncImage(url: url) { $0.resizable().scaledToFit() } placeholder: { Color.clear }.padding(4) }
            }.frame(width: 88, height: 60).clipShape(RoundedRectangle(cornerRadius: 10))
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) { UpdTag(text: tag.0, color: tag.1); Text(u.date).font(.caption2).foregroundStyle(Palette.mute) }
                Text(u.title.replacingOccurrences(of: "New: ", with: "")).font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ink).lineLimit(2)
                if let d = u.detail, !d.isEmpty { Text(d).font(.caption).foregroundStyle(Palette.mute).lineLimit(2) }
            }
            Spacer(minLength: 0)
        }
        .padding(12).background(Palette.panel, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Palette.line, lineWidth: 1))
        .padding(.horizontal, 16).padding(.vertical, 5)
    }
}

private struct UpdSkeleton: View {
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 8) {
                RoundedRectangle(cornerRadius: 6).fill(Palette.panel2).frame(width: 110, height: 12)
                RoundedRectangle(cornerRadius: 6).fill(Palette.panel2).frame(height: 14)
                RoundedRectangle(cornerRadius: 6).fill(Palette.panel2).frame(width: 180, height: 14)
            }
            Spacer(minLength: 0)
            RoundedRectangle(cornerRadius: 12).fill(Palette.panel2).frame(width: 96, height: 72)
        }.padding(.horizontal, 16).padding(.vertical, 12)
    }
}

private struct UpdEmpty: View {
    let title: String; let sub: String
    var body: some View {
        VStack(spacing: 4) {
            Text(title).font(.subheadline.weight(.semibold)).foregroundStyle(Palette.ink)
            Text(sub).font(.caption).foregroundStyle(Palette.mute)
        }.frame(maxWidth: .infinity).padding(.horizontal, 24).padding(.vertical, 36).multilineTextAlignment(.center)
    }
}
