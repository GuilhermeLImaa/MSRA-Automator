import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PIL import Image

def generate_icons():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(base_dir, "app_icon.svg")
    png_path = os.path.join(base_dir, "app_icon.png")
    ico_path = os.path.join(base_dir, "app_icon.ico")

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        print("SVG invalido!")
        return False

    # Renderiza PNG 512x512
    image = QImage(512, 512, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    image.save(png_path, "PNG")
    print("app_icon.png gerado com sucesso!")

    # Renderiza tamanhos ICO (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
    ico_images = []
    for size in [16, 32, 48, 64, 128, 256]:
        img_size = QImage(size, size, QImage.Format.Format_ARGB32)
        img_size.fill(0)
        p = QPainter(img_size)
        renderer.render(p)
        p.end()
        temp_png = os.path.join(base_dir, f"temp_{size}.png")
        img_size.save(temp_png, "PNG")
        pil_img = Image.open(temp_png)
        ico_images.append(pil_img)

    # Salva arquivo ICO multi-resolucao
    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in ico_images],
        append_images=ico_images[1:]
    )

    # Limpa arquivos temporarios
    for size in [16, 32, 48, 64, 128, 256]:
        temp_png = os.path.join(base_dir, f"temp_{size}.png")
        if os.path.exists(temp_png):
            os.remove(temp_png)

    print("app_icon.ico gerado com sucesso!")
    return True

if __name__ == "__main__":
    generate_icons()
