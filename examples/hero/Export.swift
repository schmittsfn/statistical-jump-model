import SwiftUI

@main
struct Export {
    @MainActor
    static func main() throws {
        guard CommandLine.arguments.count == 2 else {
            throw NSError(domain: "HeroExport", code: 1, userInfo: [NSLocalizedDescriptionKey: "Supply the output PNG path."])
        }
        let renderer = ImageRenderer(content: HeroView())
        renderer.scale = 2
        guard let image = renderer.cgImage else {
            throw NSError(domain: "HeroExport", code: 2, userInfo: [NSLocalizedDescriptionKey: "SwiftUI image rendering failed."])
        }
        let bitmap = NSBitmapImageRep(cgImage: image)
        guard let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "HeroExport", code: 3, userInfo: [NSLocalizedDescriptionKey: "PNG encoding failed."])
        }
        try png.write(to: URL(filePath: CommandLine.arguments[1]), options: .atomic)
        print("Exported \(image.width) × \(image.height) PNG")
    }
}
