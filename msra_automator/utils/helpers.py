import subprocess
from PyQt6.QtWidgets import QApplication

def copy_to_clipboard(text: str) -> bool:
    """
    Copia texto para a Área de Transferência preservando caracteres UTF-8 e acentuação em português.
    Executa tanto a API nativa do PyQt (QApplication.clipboard) quanto o clip.exe do Windows em UTF-16LE,
    garantindo sincronização imediata com a área de transferência do sistema operacional.
    """
    if text is None:
        text = ""

    pyqt_ok = False
    try:
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
            pyqt_ok = True
    except Exception:
        pass

    clip_ok = False
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(
            'clip',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            shell=True
        )
        p.communicate(input=text.encode('utf-16le'))
        clip_ok = True
    except Exception:
        pass

    return pyqt_ok or clip_ok
