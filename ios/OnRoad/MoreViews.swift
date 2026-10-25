import MapKit
import SwiftUI

// MARK: - Offers

struct OffersView: View {
    @EnvironmentObject var state: AppState
    @Environment(\.openURL) var openURL
    @State private var all: [Offer]?
    @State private var failed = false
    @State private var brands: Set<String> = []
    @State private var sort = "benefit"

    var shown: [Offer] {
        let l = (all ?? []).filter { brands.isEmpty || brands.contains($0.brandSlug ?? "") }
        switch sort {
        case "ending": return l.sorted { ($0.validUntil ?? "9999") < ($1.validUntil ?? "9999") }
        case "brand": return l.sorted { ($0.brandName ?? "") < ($1.brandName ?? "") }
        default: return l.sorted { ($0.amountInr ?? 0) > ($1.amountInr ?? 0) }
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                Label("Bike and scooter makers don't publish offers online. Open a bike and ask for dealer quotes.", systemImage: "tag")
                    .font(.caption).foregroundStyle(Palette.mute).padding(12).background(Palette.panel2).clipShape(RoundedRectangle(cornerRadius: 14))
                let names = Dictionary((all ?? []).map { ($0.brandSlug ?? "", $0.brandName ?? "") }, uniquingKeysWith: { a, _ in a })
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(names.keys.sorted(), id: \.self) { slug in
                            Pill(text: names[slug] ?? slug, on: brands.contains(slug)) { toggle(&brands, slug) }
                        }
                    }
                }
                if failed { ErrorView(message: "Couldn't reach OnRoad.") { Task { await load() } } }
                else if all == nil { ProgressView().frame(maxWidth: .infinity).padding(30) }
                else if shown.isEmpty { VStack { Art(name: "empty-offers"); Text("No manufacturer offers listed for \(state.city) right now.").foregroundStyle(Palette.mute) }.frame(maxWidth: .infinity) }
                ForEach(shown) { o in
                    Button { if let u = o.sourceUrl.flatMap(URL.init) { openURL(u) } } label: { OfferTile(o: o) }.buttonStyle(.plain)
                }
            }.padding(16)
        }
        .background(Palette.night)
        .navigationTitle("Offers")
        .toolbar {
            Menu { Picker("Sort", selection: $sort) { Text("Biggest benefit").tag("benefit"); Text("Ending soon").tag("ending"); Text("Brand A–Z").tag("brand") } }
                label: { Image(systemName: "arrow.up.arrow.down") }
        }
        .task(id: state.city) { await load() }
        .refreshable { await load() }
    }

    func load() async {
        failed = false
        do { all = try await API.shared.get("api/offers", ["city": state.city, "limit": "200"]) } catch { failed = true }
    }
}

// MARK: - Showrooms

struct ShowroomsView: View {
    @EnvironmentObject var state: AppState
    @State private var bike = false
    @State private var list: [Dealer]?
    @State private var failed = false
    @State private var sort = "near"

    var shown: [Dealer] {
        guard let list else { return [] }
        return sort == "near" ? list : list.sorted { ($0.googleRating ?? $0.rating ?? 0) > ($1.googleRating ?? $1.rating ?? 0) }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                Button { state.locate() } label: {
                    HStack {
                        Image(systemName: "location.fill").foregroundStyle(Palette.electric)
                        VStack(alignment: .leading) {
                            Text(state.coord == nil ? "Around \(state.city)" : "Near you").fontWeight(.semibold)
                            Text("Tap to use your exact location").font(.caption).foregroundStyle(Palette.mute)
                        }
                        Spacer()
                    }.padding(14).background(Palette.panel).clipShape(RoundedRectangle(cornerRadius: 16))
                }.buttonStyle(.plain)
                if let p = state.locationProblem { Text(p).font(.caption).foregroundStyle(Palette.amber) }
                HStack {
                    Picker("", selection: $bike) { Text("Cars").tag(false); Text("Bikes").tag(true) }.pickerStyle(.segmented)
                    Picker("", selection: $sort) { Text("Nearest").tag("near"); Text("Top rated").tag("rated") }.pickerStyle(.segmented)
                }
                if failed { ErrorView(message: "Couldn't reach OnRoad.") { Task { await load() } } }
                else if list == nil { ProgressView().frame(maxWidth: .infinity).padding(30) }
                else if shown.isEmpty { VStack { Art(name: "empty-showrooms"); Text("No listed showroom within about 300 km.").foregroundStyle(Palette.mute) }.frame(maxWidth: .infinity) }
                ForEach(shown) { d in DealerCard(d: d) }
            }.padding(16)
        }
        .background(Palette.night)
        .navigationTitle("Showrooms")
        .task(id: "\(state.city)-\(bike)-\(state.coord?.latitude ?? 0)") { await load() }
    }

    func load() async {
        failed = false; list = nil
        var lat = state.coord?.latitude, lng = state.coord?.longitude
        if lat == nil, let cities: [City] = try? await API.shared.get("api/cities"), let c = cities.first(where: { $0.name == state.city }) {
            lat = c.lat; lng = c.lng
        }
        guard let lat, let lng else { failed = true; return }
        do { list = try await API.shared.get("api/dealers/near", ["lat": String(lat), "lng": String(lng), "vehicle_type": bike ? "bike" : "car"]) }
        catch { failed = true }
    }
}

struct DealerCard: View {
    let d: Dealer
    @Environment(\.openURL) var openURL
    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(d.brandName ?? "").font(.caption.weight(.semibold)).foregroundStyle(Palette.ignition)
                    Spacer()
                    if let km = d.distanceKm { Text(String(format: "%.1f km", km)).font(.caption.bold()).foregroundStyle(Palette.electric) }
                }
                Text(d.name).font(.headline).lineLimit(2)
                Text([d.address, d.city].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: ", ")).font(.caption).foregroundStyle(Palette.mute).lineLimit(2)
                HStack(spacing: 12) {
                    if let g = d.googleRating { Text(String(format: "★ %.1f", g)).bold().foregroundColor(Palette.amber) + Text(" Google (\(d.googleCount ?? 0))").font(.caption).foregroundColor(Palette.mute) }
                    if let r = d.rating, (d.ratingCount ?? 0) > 0 { Text(String(format: "★ %.1f", r)).bold().foregroundColor(Palette.good) + Text(" \(d.ratingCount ?? 0) OnRoad").font(.caption).foregroundColor(Palette.mute) }
                }
                HStack(spacing: 8) {
                    if let ph = d.phone?.split(whereSeparator: { ",/;".contains($0) }).first,
                       let u = URL(string: "tel:" + ph.filter { $0.isNumber || $0 == "+" }) {
                        Button { openURL(u) } label: { Label("Call", systemImage: "phone.fill").frame(maxWidth: .infinity) }.buttonStyle(.bordered).tint(Palette.good)
                    }
                    if let la = d.lat, let lo = d.lng, let u = URL(string: "https://maps.apple.com/?daddr=\(la),\(lo)") {
                        Button { openURL(u) } label: { Label("Directions", systemImage: "arrow.triangle.turn.up.right.diamond.fill").frame(maxWidth: .infinity) }
                            .buttonStyle(.bordered).tint(Palette.electric)
                    }
                }
            }
        }
    }
}

// MARK: - Finder

struct FinderView: View {
    @EnvironmentObject var state: AppState
    @State private var bike = false
    @State private var budget = 12.0
    @State private var usage = "mixed"
    @State private var fuels: Set<String> = []
    @State private var bodies: Set<String> = []
    @State private var res: [Reco]?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Picker("", selection: $bike) { Text("Car").tag(false); Text("Bike / scooter").tag(true) }.pickerStyle(.segmented)
                Card { VStack(alignment: .leading) {
                    Text("ON-ROAD BUDGET").font(.caption).foregroundStyle(Palette.mute)
                    Text(String(format: "Up to ₹%.1f L", budget)).font(.title.bold())
                    Slider(value: $budget, in: bike ? 0.5...8 : 3...80, step: bike ? 0.1 : 0.5)
                } }
                HStack { ForEach(["city", "mixed", "highway"], id: \.self) { k in
                    Pill(text: ["city": "Mostly city", "mixed": "City + highway", "highway": "Long drives"][k] ?? k, on: usage == k) { usage = k } } }
                Text("Fuel").font(.headline)
                HStack { ForEach(bike ? ["Petrol", "Electric"] : ["Petrol", "Diesel", "CNG", "Hybrid", "Electric"], id: \.self) { x in Pill(text: x, on: fuels.contains(x)) { toggle(&fuels, x) } } }
                if !bike {
                    Text("Body type").font(.headline)
                    ScrollView(.horizontal, showsIndicators: false) { HStack { ForEach(["SUV", "Hatchback", "Sedan", "MUV"], id: \.self) { x in Pill(text: x, on: bodies.contains(x)) { toggle(&bodies, x) } } } }
                }
                if let r = res {
                    Text(r.isEmpty ? "No matches. Try a higher budget or fewer filters." : "Top \(r.count) of \(r.first?.pool ?? r.count) matches").font(.headline)
                    ForEach(Array(r.enumerated()), id: \.element.id) { i, x in
                        NavigationLink { ModelView(id: x.id) } label: {
                            Card { VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    RemoteImage(url: x.imageUrl, width: 480).frame(width: 110, height: 70)
                                    VStack(alignment: .leading) {
                                        Text("#\(i + 1) · \(x.matchScore ?? 0)% match").font(.caption.bold()).foregroundStyle(i == 0 ? Palette.ignition : Palette.electric)
                                        Text("\(x.brand ?? "") \(x.name)").font(.headline).lineLimit(1)
                                        Text(x.variant ?? "").font(.caption).foregroundStyle(Palette.mute).lineLimit(1)
                                        Text(rupees(x.fromInr) + " on-road").font(.subheadline.bold())
                                    }
                                }
                                ForEach(x.reasons ?? [], id: \.self) { Label($0, systemImage: "checkmark.circle.fill").font(.caption).foregroundStyle(Palette.ink) }
                                ForEach(x.warnings ?? [], id: \.self) { Label($0, systemImage: "exclamationmark.triangle.fill").font(.caption).foregroundStyle(Palette.amber) }
                            } }
                        }.buttonStyle(.plain)
                    }
                } else { ProgressView().frame(maxWidth: .infinity).padding(20) }
            }.padding(16)
        }
        .background(Palette.night)
        .navigationTitle(bike ? "Find my bike" : "Find my car")
        .onChange(of: bike) { b in budget = b ? 1.5 : 12; fuels = []; bodies = [] }
        .task(id: "\(state.city)-\(bike)-\(budget)-\(usage)-\(fuels.sorted())-\(bodies.sorted())") {
            try? await Task.sleep(nanoseconds: 300_000_000)
            res = nil
            res = (try? await API.shared.get("api/recommendations", [
                "city": state.city, "vehicle_type": bike ? "bike" : "car", "budget": String(Int(budget * 100_000)), "usage": usage,
                "fuel": fuels.isEmpty ? nil : fuels.joined(separator: ","), "body": bodies.isEmpty ? nil : bodies.joined(separator: ","),
                "priorities": "value,safety", "limit": "12"])) ?? []
        }
    }
}

// MARK: - Profile / sign in

struct LoginIn: Encodable { let email: String; let password: String }
struct SignupIn: Encodable { let name: String; let email: String; let phone: String?; let password: String; var role = "buyer" }

struct ProfileView: View {
    @EnvironmentObject var state: AppState
    @State private var signup = false
    @State private var name = ""
    @State private var email = ""
    @State private var pw = ""
    @State private var msg: String?
    @State private var busy = false
    @State private var pickingCity = false
    @AppStorage("appearance") private var appearance = "system"

    var body: some View {
        Form {
            if let a = state.account {
                Section { VStack(alignment: .leading) { Text(a.name).font(.title2.bold()); Text(a.email).foregroundStyle(Palette.mute) } }
                Section {
                    Button("Sign out", role: .destructive) {
                        Task {
                            let _: OK? = try? await API.shared.post("api/auth/logout", [String: String]())
                            HTTPCookieStorage.shared.cookies?.forEach { HTTPCookieStorage.shared.deleteCookie($0) }
                            state.account = nil
                        }
                    }
                }
            } else {
                Section {
                    Picker("", selection: $signup) { Text("Sign in").tag(false); Text("Create account").tag(true) }.pickerStyle(.segmented)
                    if signup { TextField("Full name", text: $name).textContentType(.name) }
                    TextField("Email", text: $email).textContentType(.emailAddress).keyboardType(.emailAddress).textInputAutocapitalization(.never)
                    SecureField("Password (8+ characters)", text: $pw).textContentType(signup ? .newPassword : .password)
                    if let msg { Text(msg).foregroundStyle(Palette.ignition) }
                    Button(busy ? "Please wait…" : (signup ? "Create account" : "Sign in")) { Task { await submit() } }.disabled(busy)
                } footer: { Text("Save cars, get dealer quotes and rate the showroom you bought from.") }
            }
            Section("Appearance") {
                Picker("Theme", selection: $appearance) { Text("Same as phone").tag("system"); Text("Light").tag("light"); Text("Dark").tag("dark") }
                    .pickerStyle(.segmented)
            }
            Section("City") {
                Button { pickingCity = true } label: { HStack { Text(state.city); Spacer(); Image(systemName: "chevron.right").foregroundStyle(Palette.mute) } }
            }
            Section("About") {
                Text("Prices, specs and offers come from each manufacturer's own website, refreshed every few hours.").font(.caption).foregroundStyle(Palette.mute)
            }
        }
        .navigationTitle("Profile")
        .sheet(isPresented: $pickingCity) { CityPicker() }
    }

    func submit() async {
        msg = nil
        guard email.contains("@") else { msg = "Enter a valid email"; return }
        guard pw.count >= 8 else { msg = "Password needs at least 8 characters"; return }
        if signup && name.trimmingCharacters(in: .whitespaces).isEmpty { msg = "Enter your name"; return }
        busy = true; defer { busy = false }
        do {
            if signup {
                state.account = try await API.shared.post("api/auth/signup", SignupIn(name: name, email: email, phone: nil, password: pw))
            } else {
                state.account = try await API.shared.post("api/auth/login", LoginIn(email: email, password: pw))
            }
            state.askForNotifications()              // re-sends the push token, now tied to this account
        } catch { msg = error.localizedDescription }
    }
}
