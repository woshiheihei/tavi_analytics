# Development slicerrc (auto-runs on Slicer startup when used)
# Original dev script preserved from previous .slicerrc.py
import slicer  # type: ignore
import qt  # type: ignore

# Set Slicer window to maximized
slicer.util.mainWindow().showMaximized()

# Collapse the Data Probe (bottom-left) by default on startup
# Uses a singleShot to ensure UI is ready before accessing the widget

def _collapseDataProbe():
    try:
        mw = slicer.util.mainWindow()
        w = slicer.util.findChild(mw, name='DataProbeCollapsibleWidget')
        if w is not None and hasattr(w, 'collapsed'):
            w.collapsed = True
    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to collapse Data Probe: {e}')

qt.QTimer.singleShot(0, _collapseDataProbe)

# Quick restart shortcut: Ctrl+Shift+R to call slicer.util.restart()
def slicerQuickRestart():
    """Clears the scene and restarts Slicer."""
    print("--- Executing Quick Restart ---")
    slicer.util.restart()

def _setupQuickRestartShortcut():
    try:
        mw = slicer.util.mainWindow()
        if not mw:
            return
        # Avoid duplicate shortcuts if this file is reloaded in the same session
        if hasattr(slicer, 'quickRestartShortcut') and slicer.quickRestartShortcut is not None:
            return
        shortcut = qt.QShortcut(mw)
        shortcut.setKey(qt.QKeySequence("Ctrl+Shift+R"))
        shortcut.connect('activated()', slicerQuickRestart)
        slicer.quickRestartShortcut = shortcut
        print("Custom shortcut 'Ctrl+Shift+R' for quick restart has been loaded.")
    except Exception as e:
        print(f"Failed to set up quick restart shortcut: {e}")

qt.QTimer.singleShot(0, _setupQuickRestartShortcut)

# Set all 3D views background to black on startup and keep it on layout changes
def _applyBlack3DBackground():
    try:
        lm = slicer.app.layoutManager()
        if lm is None:
            return
        black = qt.QColor(0, 0, 0)

        # Try preferred count-based iteration first
        updated = 0
        count = None
        try:
            count = lm.threeDViewCount() if callable(getattr(lm, 'threeDViewCount', None)) else getattr(lm, 'threeDViewCount', None)
        except Exception:
            count = None

        def _updateIndex(i):
            try:
                w = lm.threeDWidget(i)
                if not w:
                    return False
                # Set on MRML view node to persist across re-bindings
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
                # Use QColor API on the view widget
                try:
                    v.setBackgroundColor(black)
                    v.setBackgroundColor2(black)
                except Exception:
                    pass
                # Disable gradient if available for solid black
                try:
                    v.setGradientBackground(False)
                except Exception:
                    pass
                # Disable skybox if the build supports it
                if hasattr(v, 'setSkyboxEnabled'):
                    try:
                        v.setSkyboxEnabled(False)
                    except Exception:
                        pass
                # Force a repaint/render so it takes effect immediately
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

        if isinstance(count, int) and count > 0:
            for i in range(count):
                if _updateIndex(i):
                    updated += 1
        else:
            i = 0
            while True:
                if not _updateIndex(i):
                    break
                updated += 1
                i += 1
        # Optional: print once for visibility
        if updated:
            print(f"3D background set to black for {updated} view(s)")
    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to set 3D background: {e}')


def _setupBlack3DBackground():
    try:
        _applyBlack3DBackground()
        lm = slicer.app.layoutManager()
        if not lm:
            return
        # Avoid duplicate connections across reloads
        if not hasattr(slicer, 'black3DBackgroundConnected') or not slicer.black3DBackgroundConnected:
            try:
                lm.connect('layoutChanged()', _applyBlack3DBackground)
                slicer.black3DBackgroundConnected = True
            except Exception:
                # As a fallback, re-apply shortly after to catch late UI
                qt.QTimer.singleShot(200, _applyBlack3DBackground)
        # Ensure we also re-apply after full app startup completes
        if not hasattr(slicer, 'black3DStartupConnected') or not slicer.black3DStartupConnected:
            try:
                slicer.app.connect('startupCompleted()', _applyBlack3DBackground)
                slicer.black3DStartupConnected = True
            except Exception:
                pass
        # Optional: when scenes are imported, ensure background remains black
        try:
            if not hasattr(slicer, 'black3DSceneObserverTag') or slicer.black3DSceneObserverTag is None:
                def _onSceneEndImport(caller, event):
                    qt.QTimer.singleShot(0, _applyBlack3DBackground)
                slicer.black3DSceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndImportEvent, _onSceneEndImport)
        except Exception:
            pass
    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to set up black 3D background: {e}')


# Hide Slicer branding/logos on startup
def _hideSlicerBranding():
    """Hide Slicer logos, corner annotations, and branding elements."""
    try:
        lm = slicer.app.layoutManager()
        if lm is None:
            return

        # Clear overlays for all 3D views
        for i in range(lm.threeDViewCount):
            try:
                v = lm.threeDWidget(i).threeDView()
                if hasattr(v, 'setCornerAnnotationText'):
                    v.setCornerAnnotationText('')
                if hasattr(v, 'setFPSVisible'):
                    v.setFPSVisible(False)
            except Exception:
                pass

        # Clear overlays for standard slice views
        for name in ['Red', 'Green', 'Yellow']:
            try:
                sv = lm.sliceWidget(name).sliceView()
                if hasattr(sv, 'setCornerAnnotationText'):
                    sv.setCornerAnnotationText('')
                if hasattr(sv, 'setFPSVisible'):
                    sv.setFPSVisible(False)
            except Exception:
                pass

        # Hide any QLabel that looks like a logo/pixmap in the main window
        mw = slicer.util.mainWindow()
        hidden_count = 0
        for lbl in mw.findChildren(qt.QLabel):
            try:
                pm = lbl.pixmap() if callable(getattr(lbl, 'pixmap', None)) else getattr(lbl, 'pixmap', None)
                txt = lbl.text() if callable(getattr(lbl, 'text', None)) else getattr(lbl, 'text', '') or ''
                oname = lbl.objectName() if callable(getattr(lbl, 'objectName', None)) else getattr(lbl, 'objectName', '') or ''
                if (pm and hasattr(pm, 'isNull') and not pm.isNull()) or ('slicer' in txt.lower()) or ('logo' in oname.lower()):
                    lbl.setVisible(False)
                    hidden_count += 1
            except Exception:
                pass

        # Hide status bar and clear window icon
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

        if hidden_count > 0:
            print(f"Slicer branding hidden: {hidden_count} logo elements removed")

    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to hide Slicer branding: {e}')

def _setupBrandingHider():
    """Set up logo hiding to run on startup and layout changes."""
    try:
        # Apply immediately
        _hideSlicerBranding()
        
        # Re-apply on layout changes (in case new views are created)
        lm = slicer.app.layoutManager()
        if lm and not hasattr(slicer, 'brandingHiderConnected'):
            try:
                lm.connect('layoutChanged()', _hideSlicerBranding)
                slicer.brandingHiderConnected = True
            except Exception:
                pass

        # Re-apply after startup completes
        if not hasattr(slicer, 'brandingHiderStartupConnected'):
            try:
                slicer.app.connect('startupCompleted()', _hideSlicerBranding)
                slicer.brandingHiderStartupConnected = True
            except Exception:
                pass

    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to set up branding hider: {e}')

# Hide branding after UI is ready
qt.QTimer.singleShot(100, _setupBrandingHider)

# Ensure UI is initialized before applying background changes
qt.QTimer.singleShot(0, _setupBlack3DBackground)

# Auto-start Web Server module (development convenience)
def _startWebServer():
    """Automatically start the Web Server module on Slicer startup."""
    try:
        try:
            slicer.util.selectModule('WebServer')
            print("WebServer module selected in UI")
        except Exception as e:
            print(f"Could not select WebServer module: {e}")
            return
        qt.QTimer.singleShot(500, _startWebServerLogic)
    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to start Web Server: {e}')
        print(f"Failed to start Web Server: {e}")


def _startWebServerLogic():
    """Start the Web Server logic after module is loaded."""
    try:
        webServerModule = None
        if hasattr(slicer.modules, 'webserver'):
            webServerModule = slicer.modules.webserver
        elif hasattr(slicer.modules, 'WebServer'):
            webServerModule = slicer.modules.WebServer
        if webServerModule:
            widget = webServerModule.widgetRepresentation()
            if widget:
                for button in widget.findChildren(qt.QPushButton):
                    if 'start' in button.text.lower() and 'server' in button.text.lower():
                        button.click()
                        print("Web Server start button clicked")
                        qt.QTimer.singleShot(2000, _switchToTaviAnalytics)
                        return
                    elif 'start' in button.text.lower():
                        button.click()
                        print("Start button clicked")
                        qt.QTimer.singleShot(2000, _switchToTaviAnalytics)
                        return
        if webServerModule and hasattr(webServerModule, 'logic'):
            logic = webServerModule.logic()
            methods_to_try = ['startServer', 'start', 'StartServer', 'Start']
            for method_name in methods_to_try:
                if hasattr(logic, method_name):
                    try:
                        if method_name in ['startServer', 'StartServer']:
                            getattr(logic, method_name)(2016)
                        else:
                            getattr(logic, method_name)()
                        print(f"Web Server started using {method_name}")
                        qt.QTimer.singleShot(2000, _switchToTaviAnalytics)
                        return
                    except Exception as e:
                        print(f"Failed to start with {method_name}: {e}")
                        continue
        try:
            mw = slicer.util.mainWindow()
            for button in mw.findChildren(qt.QPushButton):
                button_text = button.text.lower()
                if ('start' in button_text and 'server' in button_text) or \
                   ('web' in button_text and 'server' in button_text):
                    button.click()
                    print("Web Server button found and clicked in main window")
                    qt.QTimer.singleShot(2000, _switchToTaviAnalytics)
                    return
        except Exception as e:
            print(f"Failed to find start button in main window: {e}")
        print("Could not automatically start Web Server. Switching to tavi_analytics module.")
        _switchToTaviAnalytics()
    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to start Web Server logic: {e}')
        print(f"Failed to start Web Server logic: {e}")
        _switchToTaviAnalytics()


def _switchToTaviAnalytics():
    """Switch to the tavi_analytics module."""
    try:
        slicer.util.selectModule('tavi_analytics')
        print("Switched to tavi_analytics module")
    except Exception as e:
        import logging
        logging.getLogger('slicer').warning(f'Failed to switch to tavi_analytics module: {e}')
        print(f"Failed to switch to tavi_analytics module: {e}")

# Start Web Server after UI is fully initialized (dev only)
qt.QTimer.singleShot(500, _startWebServer)
