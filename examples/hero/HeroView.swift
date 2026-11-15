import SwiftUI

/// Fixed-size editorial illustration; curves are schematic, not market data.
struct HeroView: View {
    private let navy = Color(red: 0.07, green: 0.16, blue: 0.25)
    private let blue = Color(red: 0.31, green: 0.48, blue: 0.61)
    private let red = Color(red: 0.62, green: 0.22, blue: 0.22)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Rectangle().fill(navy).frame(height: 4)
            HStack(alignment: .top, spacing: 46) {
                VStack(alignment: .leading, spacing: 24) {
                    Text("MARKET REGIMES / 02").font(.system(size: 12, weight: .semibold)).tracking(2.5).foregroundStyle(blue)
                    Text("Conditions change.\nSo does the risk.").font(.system(size: 39, design: .serif)).foregroundStyle(navy).lineSpacing(3)
                    Rectangle().fill(red).frame(width: 38, height: 2)
                    Text("A persistent change in behaviour\ncan make yesterday’s approach less useful.").font(.system(size: 16)).lineSpacing(6).foregroundStyle(navy.opacity(0.8))
                    Spacer()
                }.frame(width: 360, alignment: .leading)
                VStack(spacing: 15) {
                    Canvas { context, size in
                        for fraction in [0.25, 0.5, 0.75] {
                            var grid = Path()
                            grid.move(to: CGPoint(x: 0, y: size.height * fraction))
                            grid.addLine(to: CGPoint(x: size.width, y: size.height * fraction))
                            context.stroke(grid, with: .color(navy.opacity(0.08)), lineWidth: 1)
                        }
                        let transition = size.width * 0.55
            context.fill(Path(CGRect(x: transition, y: 20, width: size.width - transition, height: size.height - 40)), with: .color(red.opacity(0.055)))
            var divider = Path(); divider.move(to: CGPoint(x: transition, y: 20)); divider.addLine(to: CGPoint(x: transition, y: size.height - 20))
            context.stroke(divider, with: .color(red.opacity(0.4)), style: StrokeStyle(lineWidth: 1, dash: [4, 5]))
            for segment in 0..<2 {
                var path = Path()
                let range = segment == 0 ? 0...132 : 132...240
                for step in range {
                    let t = Double(step) / 240
                    let y = t <= 0.55 ? 0.78 - t * 0.88 + 0.025 * sin(t * 75) : 0.296 + (t - 0.55) * 0.62 + 0.065 * sin((t - 0.55) * 72)
                    let point = CGPoint(x: t * size.width, y: y * size.height)
                    if step == range.lowerBound { path.move(to: point) } else { path.addLine(to: point) }
                }
                context.stroke(path, with: .color(segment == 0 ? navy : red), style: StrokeStyle(lineWidth: 2.6, lineCap: .round))
            }
                    }.frame(height: 285)
                    HStack {
                        Text("More favourable conditions")
                        Spacer()
                        Text("Less favourable conditions")
                    }.font(.system(size: 12)).foregroundStyle(navy.opacity(0.65))
                }.padding(.top, 18)
            }.padding(.horizontal, 48).padding(.top, 42)
            Spacer(minLength: 24)
            Rectangle().fill(navy.opacity(0.15)).frame(height: 1).padding(.horizontal, 48)
            HStack {
                Text("RESEARCH / CONCEPTUAL ILLUSTRATION").tracking(1.4)
                Spacer()
                Text("Schematic only · not a forecast")
            }.font(.system(size: 10)).foregroundStyle(navy.opacity(0.65)).padding(.horizontal, 48).padding(.vertical, 22)
        }.frame(width: 1200, height: 470).background(Color(red: 0.98, green: 0.977, blue: 0.966))
            .environment(\.colorScheme, .light)
    }
}
