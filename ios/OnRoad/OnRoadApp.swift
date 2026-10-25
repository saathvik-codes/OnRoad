import CoreLocation
import FirebaseCore
import FirebaseMessaging
import SwiftUI
import UserNotifications

/// Firebase (Analytics, Crashlytics, Messaging) and push registration.
final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate, MessagingDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        FirebaseApp.configure()
        Messaging.messaging().delegate = self
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
    }

    /// The phone's FCM token goes to the server (price drops on saved cars, dealer quotes).
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let fcmToken else { return }
        Task { let _: OK? = try? await API.shared.post("api/me/push-token", ["token": fcmToken, "platform": "ios"]) }
    }

    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification) async -> UNNotificationPresentationOptions {
        [.banner, .sound]
    }
}

/// What every screen shares: the chosen city, the signed-in buyer, the phone's location.
@MainActor
final class AppState: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var city: String = UserDefaults.standard.string(forKey: "city") ?? "Hyderabad" {
        didSet { UserDefaults.standard.set(city, forKey: "city") }
    }
    @Published var coord: CLLocationCoordinate2D?
    @Published var account: Account?
    @Published var locationProblem: String?
    private let lm = CLLocationManager()

    override init() {
        super.init()
        lm.delegate = self
        lm.desiredAccuracy = kCLLocationAccuracyHundredMeters
        Task { self.account = try? await API.shared.get("api/auth/me") }
    }

    func locate() {
        locationProblem = nil
        switch lm.authorizationStatus {
        case .notDetermined: lm.requestWhenInUseAuthorization()
        case .denied, .restricted: locationProblem = "Location is off for OnRoad. Turn it on in Settings, or pick your city."
        default: lm.requestLocation()
        }
    }

    /// Picking a city moves the search there too (its centre), so showrooms and prices follow the city.
    func choose(_ c: City) {
        city = c.name
        if let la = c.lat, let lo = c.lng { coord = CLLocationCoordinate2D(latitude: la, longitude: lo) }
    }

    func askForNotifications() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { ok, _ in
            if ok { DispatchQueue.main.async { UIApplication.shared.registerForRemoteNotifications() } }
        }
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        Task { @MainActor in
            if manager.authorizationStatus == .authorizedWhenInUse || manager.authorizationStatus == .authorizedAlways { manager.requestLocation() }
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let l = locations.last else { return }
        Task { @MainActor in
            self.coord = l.coordinate
            // nearest OnRoad city to the phone
            if let cities: [City] = try? await API.shared.get("api/cities") {
                let best = cities.min { a, b in
                    let da = pow((a.lat ?? 0) - l.coordinate.latitude, 2) + pow((a.lng ?? 0) - l.coordinate.longitude, 2)
                    let db = pow((b.lat ?? 0) - l.coordinate.latitude, 2) + pow((b.lng ?? 0) - l.coordinate.longitude, 2)
                    return da < db
                }
                if let best { self.city = best.name }
            }
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        Task { @MainActor in self.locationProblem = "Couldn't get your location. Pick your city instead." }
    }
}

@main
struct OnRoadApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @StateObject private var state = AppState()
    @AppStorage("appearance") private var appearance = "system"     // system | light | dark, picked in Profile

    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(state).tint(Palette.ignition)
                .preferredColorScheme(appearance == "light" ? .light : appearance == "dark" ? .dark : nil)
        }
    }
}

struct RootView: View {
    @EnvironmentObject var state: AppState
    var body: some View {
        TabView {
            NavigationStack { HomeView() }.tabItem { Label("Home", systemImage: "house") }
            NavigationStack { ExploreView() }.tabItem { Label("Explore", systemImage: "square.grid.2x2") }
            NavigationStack { OffersView() }.tabItem { Label("Offers", systemImage: "tag") }
            NavigationStack { ShowroomsView() }.tabItem { Label("Showrooms", systemImage: "mappin.and.ellipse") }
            NavigationStack { ProfileView() }.tabItem { Label("Profile", systemImage: "person.crop.circle") }
        }
        .background(Palette.night)
        .task { state.askForNotifications() }
    }
}
