import SwiftUI

/// The same palette as the Android app and the website.
enum Palette {
    static let night = Color(hex: 0x05060A)
    static let panel = Color(hex: 0x0E1119)
    static let panel2 = Color(hex: 0x161A26)
    static let line = Color(hex: 0x232838)
    static let mute = Color(hex: 0x94A3B8)
    static let ink = Color(hex: 0xF1F4FA)
    static let ignition = Color(hex: 0xFF4D2E)
    static let electric = Color(hex: 0x39D0FF)
    static let good = Color(hex: 0x34D399)
    static let amber = Color(hex: 0xFFB547)
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
    }
}

/// ₹ in lakh / crore the way Indian buyers read prices.
func rupees(_ v: Int?) -> String {
    guard let v else { return "—" }
    if v >= 1_00_00_000 { return String(format: "₹%.2f Cr", Double(v) / 1e7) }
    if v >= 1_00_000 { return String(format: "₹%.2f L", Double(v) / 1e5) }
    let f = NumberFormatter(); f.numberStyle = .decimal; f.locale = Locale(identifier: "en_IN")
    return "₹" + (f.string(from: NSNumber(value: v)) ?? "\(v)")
}

func range(_ lo: Int?, _ hi: Int?) -> String {
    guard let lo else { return "Price not published" }
    if let hi, hi > lo { return "\(rupees(lo)) – \(rupees(hi))" }
    return rupees(lo)
}

struct Card<Content: View>: View {
    var padding: CGFloat = 14
    @ViewBuilder var content: Content
    var body: some View {
        content.padding(padding).frame(maxWidth: .infinity, alignment: .leading)
            .background(Palette.panel).clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Palette.line, lineWidth: 1))
    }
}

struct Chip: View {
    let text: String
    var color: Color = Palette.electric
    var body: some View {
        Text(text).font(.caption.weight(.semibold)).foregroundStyle(color)
            .padding(.horizontal, 9).padding(.vertical, 4).background(color.opacity(0.14)).clipShape(Capsule())
    }
}

struct Pill: View {
    let text: String
    let on: Bool
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            Text(text).font(.subheadline.weight(on ? .semibold : .regular)).foregroundStyle(on ? .white : Palette.mute)
                .padding(.horizontal, 14).padding(.vertical, 9).background(on ? Palette.ignition : Palette.panel2).clipShape(Capsule())
        }.buttonStyle(.plain)
    }
}

/// Every picture goes through the API's image proxy (resized, cached, no hotlink blocks), like the Android app.
struct RemoteImage: View {
    let url: String?
    var width: Int = 800
    var fit: Bool = true
    var body: some View {
        AsyncImage(url: API.shared.imageURL(url, width: width)) { phase in
            switch phase {
            case .success(let img): img.resizable().aspectRatio(contentMode: fit ? .fit : .fill)
            case .failure: Image(systemName: "car.side").font(.largeTitle).foregroundStyle(Palette.line)
            default: ProgressView().tint(Palette.mute)
            }
        }
    }
}

struct ErrorView: View {
    let message: String
    let retry: () -> Void
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: "icloud.slash").font(.largeTitle).foregroundStyle(Palette.mute)
            Text(message).foregroundStyle(Palette.mute).multilineTextAlignment(.center)
            Button("Try again", action: retry).buttonStyle(.bordered)
        }.padding(32).frame(maxWidth: .infinity)
    }
}
