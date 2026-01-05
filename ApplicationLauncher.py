from kivy.utils import platform

if platform == 'android':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout

    class MyApp(App):
        def build(self):
            from kivy_garden.webview import WebView
            layout = BoxLayout()
            layout.add_widget(WebView(url='http://127.0.0.1:5000'))
            return layout

    MyApp().run()

else:
    import webview
    webview.create_window("HomeNoteApp", "http://127.0.0.1:5000")
    webview.start()
