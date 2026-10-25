import Foundation

// MARK: - Data (the same JSON the website and the Android app read; snake_case keys are converted)

struct ModelSummary: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    var brand: String?
    var brandSlug: String?
    var bodyType: String?
    var imageUrl: String?
    var vehicleType: String?
    var fromInr: Int?
    var toInr: Int?
    var fuels: String?
    var transmissions: String?
    var variants: Int?
    var offers: Int?
    var salesRank: Int?
    var band: String?
    var logo: String?
}

struct Line: Codable, Hashable {
    let label: String
    var amountInr: Int?
    var basis: String?
    var refundable: Bool?
    var optional: Bool?
}

struct OnRoadBreakup: Codable, Hashable {
    var stateName: String?
    var exShowroomInr: Int?
    var lines: [Line]
    var totalInr: Int
    var refundableInr: Int
    var notes: [String]?
}

struct Variant: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    var fuel: String?
    var transmission: String?
    var imageUrl: String?
    var exShowroomInr: Int?
    var priceCity: String?
    var onroad: OnRoadBreakup?
}

struct Dealer: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    var brandSlug: String?
    var brandName: String?
    var address: String?
    var city: String?
    var phone: String?
    var lat: Double?
    var lng: Double?
    var distanceKm: Double?
    var rating: Double?
    var ratingCount: Int?
    var googleRating: Double?
    var googleCount: Int?
    var googleMapsUri: String?
    var photoUrl: String?
}

struct GalleryItem: Codable, Hashable {
    let url: String
    var label: String?
    var kind: String?
}

struct CrashTest: Codable, Hashable {
    var agency: String?
    var protocol_: String?
    var adultStars: Int?
    var childStars: Int?
    var sourceUrl: String?
    enum CodingKeys: String, CodingKey { case agency, protocol_ = "protocol", adultStars, childStars, sourceUrl }
}

struct Offer: Codable, Identifiable, Hashable {
    let id: Int
    var brandSlug: String?
    var brandName: String?
    var modelName: String?
    var modelImage: String?
    var title: String
    var amountInr: Int?
    var details: String?
    var validUntil: String?
    var sourceUrl: String?
    var kind: String?
}

struct ModelDetail: Codable, Identifiable {
    let id: String
    let name: String
    var brandName: String?
    var brandSlug: String?
    var bodyType: String?
    var imageUrl: String?
    var vehicleType: String?
    var brandVehicleType: String?
    var variants: [Variant]
    var dealers: [Dealer]
    var offers: [ModelOffer]?
    var crashTests: [CrashTest]?
    var gallery: [GalleryItem]?
}

struct ModelOffer: Codable, Hashable {
    var title: String
    var amountInr: Int?
    var validUntil: String?
    var details: String?
}

struct SpecRow: Codable, Hashable { var grp: String?; var key: String?; var label: String; var value: String }
struct FeatureRow: Codable, Hashable { var key: String; var label: String }
struct VariantSpecs: Codable { var specs: [SpecRow]; var features: [FeatureRow] }

struct City: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    var stateName: String?
    var lat: Double?
    var lng: Double?
}

struct Brand: Codable, Identifiable, Hashable {
    var id: String { slug }
    let slug: String
    let name: String
    var logo: String?
    var models: Int?
    var fromInr: Int?
}

struct Reco: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    var brand: String?
    var imageUrl: String?
    var fromInr: Int?
    var matchScore: Int?
    var reasons: [String]?
    var warnings: [String]?
    var variant: String?
    var transmission: String?
    var crashStars: Int?
    var bodyType: String?
    var fuels: String?
    var pool: Int?
}

struct Hit: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    var brand: String?
    var fromInr: Int?
    var note: String?
}

struct Account: Codable, Hashable { let id: Int; let email: String; var name: String; var role: String }

// MARK: - Client

enum APIError: LocalizedError {
    case http(Int, String)
    var errorDescription: String? {
        switch self { case .http(_, let m): return m }
    }
}

final class API {
    static let shared = API()
    let base = URL(string: "https://onroad-uu9c.onrender.com")!
    private let session: URLSession
    private let decoder: JSONDecoder = { let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase; return d }()
    private let encoder: JSONEncoder = { let e = JSONEncoder(); e.keyEncodingStrategy = .convertToSnakeCase; return e }()

    private init() {
        let c = URLSessionConfiguration.default
        c.httpCookieStorage = HTTPCookieStorage.shared       // the login cookie, kept across launches
        c.timeoutIntervalForRequest = 60
        session = URLSession(configuration: c)
    }

    func imageURL(_ url: String?, width: Int = 800) -> URL? {
        guard let url, !url.isEmpty else { return nil }
        if url.hasPrefix("http") {
            var c = URLComponents(url: base.appendingPathComponent("api/img"), resolvingAgainstBaseURL: false)!
            c.queryItems = [URLQueryItem(name: "w", value: "\(width)"), URLQueryItem(name: "u", value: url)]
            return c.url
        }
        return URL(string: url, relativeTo: base)
    }

    func get<T: Decodable>(_ path: String, _ query: [String: String?] = [:]) async throws -> T {
        var c = URLComponents(url: base.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        c.queryItems = query.compactMap { k, v in v.map { URLQueryItem(name: k, value: $0) } }
        return try await send(URLRequest(url: c.url!))
    }

    func post<T: Decodable, B: Encodable>(_ path: String, _ body: B) async throws -> T {
        var r = URLRequest(url: base.appendingPathComponent(path))
        r.httpMethod = "POST"
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.httpBody = try encoder.encode(body)
        return try await send(r)
    }

    private func send<T: Decodable>(_ r: URLRequest) async throws -> T {
        let (data, resp) = try await session.data(for: r)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(code) else {
            let msg = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw APIError.http(code, msg ?? "Something went wrong (\(code)).")
        }
        return try decoder.decode(T.self, from: data)
    }
}

struct OK: Decodable {}
