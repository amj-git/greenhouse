'''
    a simple Yes/No Popup
    LICENSE : MIT
'''
from kivy.uix.popup import Popup
from kivy.properties import StringProperty

from kivy.lang.builder import Builder
Builder.load_string('''
#<KvLang>
#:set fsize1 "20sp"
<YesNoPopup>:
    FloatLayout:
        
        Label:
            size_hint: 0.8, 0.6
            pos_hint: {'x': 0.1, 'y':0.4}
            text: root.message
            font_size: fsize1

        Button:
            size_hint: 0.4, 0.35
            pos_hint: {'x':0.1, 'y':0.05}
            text: 'Yes'
            on_release: root.dispatch('on_yes')
            font_size: fsize1
        
        Button:
            size_hint: 0.4, 0.35
            pos_hint: {'x':0.5, 'y':0.05}
            text: 'No'
            on_release: root.dispatch('on_no')
            font_size: fsize1

#</KvLang>
''')

class YesNoPopup(Popup):
    __events__ = ('on_yes', 'on_no')

    message = StringProperty('')

    def __init__(self, **kwargs) -> None:
        super(YesNoPopup, self).__init__(**kwargs)
        self.auto_dismiss = False
        self.title_size="20sp"
    
    def on_yes(self):
        pass
    
    def on_no(self):
        pass


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    
    class TestApp(App):
        def __init__(self, **kwargs):
            super(TestApp, self).__init__(**kwargs)
    
        def build(self):
            self.pop = pop = YesNoPopup(
                title='Popup !',
                message='OK ?',
                size_hint=(0.4, 0.3),
                pos_hint={'x':0.3, 'y':0.35}
            )
            pop.bind(
                on_yes=self._popup_yes,
                on_no=self._popup_no
            )
            root = BoxLayout()
            btn = Button(text='open')
            root.add_widget(btn)
            btn.bind(on_release=lambda btn: self.pop.open())
            return root

        def _popup_yes(self, instance):
            print(f'{instance} on_yes')
            self.pop.dismiss()

        def _popup_no(self, instance):
            print(f'{instance} on_no')
            self.pop.dismiss()

    
    TestApp().run()
