"""
Production slicerrc (no Web Server automation).
This file is loaded by Slicer on startup in production deployments.
For development with Web Server auto-start, use .slicerrc.dev.py instead.
"""
import slicer  # type: ignore
import qt  # type: ignore

# Maximize main window
slicer.util.mainWindow().showMaximized()


# Collapse the Data Probe (bottom-left) on startup
def _collapseDataProbe():
    try:
        mw = slicer.util.mainWindow()
        w = slicer.util.findChild(mw, name='DataProbeCollapsibleWidget')
        if w is not None and hasattr(w, 'collapsed'):
            w.collapsed = True
    except Exception:
        pass

qt.QTimer.singleShot(0, _collapseDataProbe)


# Quick restart shortcut: Ctrl+Shift+R
def slicerQuickRestart():
    try:
        slicer.util.restart()
    except Exception:
        pass


def _setupQuickRestartShortcut():
    try:
        mw = slicer.util.mainWindow()
        if not mw:
            return
        if hasattr(slicer, 'quickRestartShortcut') and slicer.quickRestartShortcut is not None:
            return
        shortcut = qt.QShortcut(mw)
        shortcut.setKey(qt.QKeySequence("Ctrl+Shift+R"))
        shortcut.connect('activated()', slicerQuickRestart)
        slicer.quickRestartShortcut = shortcut
    except Exception:
        pass

qt.QTimer.singleShot(0, _setupQuickRestartShortcut)


# Set all 3D views background to black and keep it on layout changes
def _applyBlack3DBackground():
    try:
        lm = slicer.app.layoutManager()
        if lm is None:
            return
        black = qt.QColor(0, 0, 0)

        def _updateIndex(i):
            try:
                w = lm.threeDWidget(i)
                if not w:
                    return False
                node = w.mrmlViewNode()
                if node:
                    try:
                        node.SetBackgroundColor(0.0, 0.0, 0.0)
                        node.SetBackgroundColor2(0.0, 0.0, 0.0)
                        node.Modified()
                    except Exception:
                        pass
                v = w.threeDView()
                if not v:
                    return False
                try:
                    v.setBackgroundColor(black)
                    v.setBackgroundColor2(black)
                except Exception:
                    pass
                try:
                    v.setGradientBackground(False)
                except Exception:
                    pass
                if hasattr(v, 'setSkyboxEnabled'):
                    try:
                        v.setSkyboxEnabled(False)
                    except Exception:
                        pass
                try:
                    if hasattr(v, 'scheduleRender'):
                        v.scheduleRender()
                    else:
                        rw = v.renderWindow() if hasattr(v, 'renderWindow') else None
                        if rw:
                            rw.Render()
                except Exception:
                    pass
                return True
            except Exception:
                return False

        count = None
        try:
            count = lm.threeDViewCount() if callable(getattr(lm, 'threeDViewCount', None)) else getattr(lm, 'threeDViewCount', None)
        except Exception:
            count = None
        if isinstance(count, int) and count > 0:
            for i in range(count):
                _updateIndex(i)
        else:
            i = 0
            while _updateIndex(i):
                i += 1
    except Exception:
        pass


def _setupBlack3DBackground():
    try:
        _applyBlack3DBackground()
        lm = slicer.app.layoutManager()
        if not lm:
            return
        if not hasattr(slicer, 'black3DBackgroundConnected') or not slicer.black3DBackgroundConnected:
            try:
                lm.connect('layoutChanged()', _applyBlack3DBackground)
                slicer.black3DBackgroundConnected = True
            except Exception:
                qt.QTimer.singleShot(200, _applyBlack3DBackground)
        if not hasattr(slicer, 'black3DStartupConnected') or not slicer.black3DStartupConnected:
            try:
                slicer.app.connect('startupCompleted()', _applyBlack3DBackground)
                slicer.black3DStartupConnected = True
            except Exception:
                pass
        if not hasattr(slicer, 'black3DSceneObserverTag') or slicer.black3DSceneObserverTag is None:
            try:
                def _onSceneEndImport(caller, event):
                    qt.QTimer.singleShot(0, _applyBlack3DBackground)
                slicer.black3DSceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndImportEvent, _onSceneEndImport)
            except Exception:
                pass
    except Exception:
        pass


# Hide Slicer branding/logos on startup
def _hideSlicerBranding():
    try:
        lm = slicer.app.layoutManager()
        if lm is None:
            return
        for i in range(lm.threeDViewCount):
            try:
                v = lm.threeDWidget(i).threeDView()
                if hasattr(v, 'setCornerAnnotationText'):
                    v.setCornerAnnotationText('')
                if hasattr(v, 'setFPSVisible'):
                    v.setFPSVisible(False)
            except Exception:
                pass
        for name in ['Red', 'Green', 'Yellow']:
            try:
                sv = lm.sliceWidget(name).sliceView()
                if hasattr(sv, 'setCornerAnnotationText'):
                    sv.setCornerAnnotationText('')
                if hasattr(sv, 'setFPSVisible'):
                    sv.setFPSVisible(False)
            except Exception:
                pass
        mw = slicer.util.mainWindow()
        for lbl in mw.findChildren(qt.QLabel):
            try:
                pm = lbl.pixmap() if callable(getattr(lbl, 'pixmap', None)) else getattr(lbl, 'pixmap', None)
                txt = lbl.text() if callable(getattr(lbl, 'text', None)) else getattr(lbl, 'text', '') or ''
                oname = lbl.objectName() if callable(getattr(lbl, 'objectName', None)) else getattr(lbl, 'objectName', '') or ''
                if (pm and hasattr(pm, 'isNull') and not pm.isNull()) or ('slicer' in txt.lower()) or ('logo' in oname.lower()):
                    lbl.setVisible(False)
            except Exception:
                pass
        try:
            sb = mw.statusBar() if callable(getattr(mw, 'statusBar', None)) else getattr(mw, 'statusBar', None)
            if sb:
                sb.setVisible(False)
        except Exception:
            pass
        try:
            mw.setWindowIcon(qt.QIcon())
        except Exception:
            pass
    except Exception:
        pass


def _setupBrandingHider():
    try:
        _hideSlicerBranding()
        lm = slicer.app.layoutManager()
        if lm and not hasattr(slicer, 'brandingHiderConnected'):
            try:
                lm.connect('layoutChanged()', _hideSlicerBranding)
                slicer.brandingHiderConnected = True
            except Exception:
                pass
        if not hasattr(slicer, 'brandingHiderStartupConnected'):
            try:
                slicer.app.connect('startupCompleted()', _hideSlicerBranding)
                slicer.brandingHiderStartupConnected = True
            except Exception:
                pass
    except Exception:
        pass

qt.QTimer.singleShot(100, _setupBrandingHider)
qt.QTimer.singleShot(0, _setupBlack3DBackground)


# Switch to the tavi_analytics module (no Web Server control in production)
def _switchToTaviAnalytics():
    try:
        slicer.util.selectModule('tavi_analytics')
    except Exception:
        pass

qt.QTimer.singleShot(500, _switchToTaviAnalytics)
