import SwiftUI

/// The OnRoad mark: the gradient ring with a lane cutting through it, as on the app icon.
struct RingMark: Shape {
    var sweep: Double
    var animatableData: Double { get { sweep } set { sweep = newValue } }
    func path(in r: CGRect) -> Path {
        var p = Path()
        let w = r.width * 0.25
        p.addArc(center: CGPoint(x: r.midX, y: r.midY), radius: r.width / 2 - w / 2, startAngle: .degrees(-200),
                 endAngle: .degrees(-200 + 360 * sweep), clockwise: false)
        return p.strokedPath(StrokeStyle(lineWidth: w))
    }
}

struct LaneMarks: View {
    let shift: CGFloat
    let color: Color
    var body: some View {
        GeometryReader { g in
            let w = g.size.width
            Path { p in
                var x = -w * 0.1 + shift.truncatingRemainder(dividingBy: w * 0.25)
                while x < w * 1.1 { p.move(to: CGPoint(x: x, y: g.size.height / 2)); p.addLine(to: CGPoint(x: x + w * 0.12, y: g.size.height / 2)); x += w * 0.25 }
            }.stroke(color, style: StrokeStyle(lineWidth: w * 0.035, lineCap: .round))
        }
    }
}

/// Launch animation: the ring draws itself, a lane races through it and dissolves, the
/// ring settles into the "o" of the wordmark while "nroad" unrolls out of it, a light streak crosses, then it fades out.
struct BrandIntro: View {
    let done: () -> Void
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @State private var sweep = 0.0
    @State private var lane = 0.0
    @State private var drive: CGFloat = 0
    @State private var settle = 0.0
    @State private var reveal = 0.0
    @State private var shine = -0.3
    @State private var tag = 0.0
    @State private var out = 1.0

    private let mark: CGFloat = 28
    private let word = "nroad"

    var body: some View {
        let scale = 3.5 - 2.5 * settle
        ZStack {
            Palette.night.ignoresSafeArea()
            VStack(spacing: 14) {
                HStack(alignment: .firstTextBaseline, spacing: 3) {
                    ZStack {
                        RingMark(sweep: sweep).fill(LinearGradient(colors: [Color(hex: 0xFFB347), Color(hex: 0xFF4D2E), Color(hex: 0xC2185B)],
                                                                 startPoint: .topLeading, endPoint: .bottomTrailing))
                        ZStack {
                            Rectangle().fill(Palette.night).frame(height: mark * 0.12)
                            LaneMarks(shift: drive * mark * 2.4, color: Palette.ink)
                        }.frame(width: mark * 1.2).rotationEffect(.degrees(-24)).opacity(lane)
                    }
                    .frame(width: mark, height: mark)
                    .scaleEffect(scale)
                    .offset(x: wordWidth / 2 * (1 - settle), y: 5)
                    (Text("n").foregroundColor(Palette.ink) + Text("road").foregroundColor(Palette.ignition))
                        .font(.system(size: 46, weight: .bold, design: .default)).tracking(-1.5)
                        .mask(alignment: .leading) { Rectangle().scaleEffect(x: reveal, y: 1, anchor: .leading) }
                        .overlay(
                            GeometryReader { g in
                                LinearGradient(colors: [.clear, .white.opacity(0.55), .clear], startPoint: .leading, endPoint: .trailing)
                                    .frame(width: g.size.width * 0.36).offset(x: g.size.width * shine - g.size.width * 0.18)
                            }.mask((Text("n") + Text("road")).font(.system(size: 46, weight: .bold)).tracking(-1.5)).allowsHitTesting(false)
                        )
                        .offset(x: -24 * (1 - reveal))
                }
                Text("The real on-road price").font(.system(size: 14, weight: .medium)).tracking(0.6).foregroundColor(Palette.mute)
                    .opacity(tag).offset(y: 8 * (1 - tag))
            }
        }
        .opacity(out)
        .contentShape(Rectangle())
        .onTapGesture(perform: done)
        .task { await play() }
    }

    private var wordWidth: CGFloat { 140 }                 // "nroad" at 46 pt bold, so the ring starts centred

    private func play() async {
        if reduceMotion { done(); return }
        func wait(_ s: Double) async { try? await Task.sleep(nanoseconds: UInt64(s * 1_000_000_000)) }
        withAnimation(.timingCurve(0.22, 1, 0.36, 1, duration: 0.48)) { sweep = 1 }
        await wait(0.45)
        withAnimation(.easeOut(duration: 0.16)) { lane = 1 }
        withAnimation(.linear(duration: 0.32)) { drive = 0.45 }
        await wait(0.32)
        withAnimation(.easeIn(duration: 0.26)) { lane = 0 }
        withAnimation(.linear(duration: 0.26)) { drive = 0.75 }
        withAnimation(.timingCurve(0.65, 0, 0.35, 1, duration: 0.52)) { settle = 1 }
        await wait(0.18)
        withAnimation(.timingCurve(0.22, 1, 0.36, 1, duration: 0.42)) { reveal = 1 }
        await wait(0.42)
        withAnimation(.linear(duration: 0.42)) { shine = 1.3 }
        withAnimation(.easeOut(duration: 0.26)) { tag = 1 }
        await wait(0.54)
        withAnimation(.easeIn(duration: 0.22)) { out = 0 }
        await wait(0.22)
        done()
    }
}
