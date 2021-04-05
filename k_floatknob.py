"""
   Floatknob
   
   Creates a popup with a knob to choose a value
   
   It embeds kivy garden.knob from https://github.com/kivy-garden/garden.knob
   
   
   
   
"""



import math

from kivy.lang          import  Builder
from kivy.uix.widget    import  Widget
from kivy.properties    import  NumericProperty, ObjectProperty, StringProperty,\
                                BooleanProperty, ReferenceListProperty, BoundedNumericProperty,\
                                ListProperty
from kivy.uix.popup import Popup

#KNOB WIDGET----------------------------------------------------------

Builder.load_string('''
<Knob>
    label: _label
    size_hint: None, None

    canvas.before:
        Color:
            rgba: self.markeroff_color
        Ellipse:
            pos: self.pos
            size: self.size[0], self.size[1]
            angle_start: 0
            angle_end: 360
            source: self.markeroff_img

        Color:
            rgba: self.marker_color
        Ellipse:
            pos: self.pos
            size: self.size[0], self.size[1]
            angle_start: self.marker_startangle
            angle_end: self._angle + self.marker_ahead if self._angle > self.marker_startangle else self.marker_startangle
            source: self.marker_img

        Color:
            rgba: self.knobimg_bgcolor
        Ellipse:
            pos: self.pos[0] + (self.size[0] * (1 - self.knobimg_size))/2, self.pos[1] + (self.size[1] * (1 - self.knobimg_size)) / 2
            size: self.size[0] * (self.knobimg_size), self.size[1] * (self.knobimg_size)

        Color:
            rgba: self.knobimg_color
        PushMatrix
        Rotate:
            angle: 360 - self._angle
            origin: self.center
        Rectangle:
            pos: self.pos[0] + (self.size[0] * (1 - self.knobimg_size)) /2, self.pos[1] + (self.size[1] * (1 - self.knobimg_size)) / 2
            size: self.size[0] * (self.knobimg_size), self.size[1] * (self.knobimg_size)
            source: self.knobimg_source

    canvas:
        PopMatrix

    Label:
        id: _label
        text: "%.1f"%(root.value)
        center: root.center
        font_size: root.font_size
        color: root.font_color''')

class Knob(Widget):
    """Class for creating a Knob widget."""

    min = NumericProperty(0)
    '''Minimum value for value :attr:`value`.
    :attr:`min` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    max = NumericProperty(100)
    '''Maximum value for value :attr:`value`.
    :attr:`max` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 100.
    '''

    range = ReferenceListProperty(min, max)
    ''' Range of the values for Knob.
    :attr:`range` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`min`, :attr:`max`).
    '''

    value = NumericProperty(0)
    '''Current value of the knob. Set :attr:`value` when creating a knob to
    set its initial position. An internal :attr:`_angle` is calculated to set
    the position of the knob.
    :attr:`value` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    step = BoundedNumericProperty(1, min=0)
    '''Step interval of knob to go from min to max. An internal
    :attr:`_angle_step` is calculated to set knob step in degrees.
    :attr:`step` is a :class:`~kivy.properties.BoundedNumericProperty`
    and defaults to 1 (min=0).
    '''

    curve = BoundedNumericProperty(1, min=1)
    '''This parameter determines the shape of the map function. It represent the
    reciprocal of a power function's exponent used to map the input value.
    So, for higher values of curve the contol is more reactive, and conversely.
    '''

    knobimg_source = StringProperty("")
    '''Path of texture image that visually represents the knob. Use PNG for
    transparency support. The texture is rendered on a centered rectangle of
    size = :attr:`size` * :attr:`knobimg_size`.
    :attr:`knobimg_source` is a :class:`~kivy.properties.StringProperty`
    and defaults to empty string.
    '''

    knobimg_color = ListProperty([1, 1, 1, 1])
    '''Color to apply to :attr:`knobimg_source` texture when loaded.
    :attr:`knobimg_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [1,1,1,1].
    '''

    show_label = BooleanProperty(True)
    ''' Shows/hides center label that show current value of knob.
    :attr:`show_label` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    font_size = StringProperty('10sp')
    ''' Font size of label.
    :attr:`font_size` is a :class:`~kivy.properties.StringProperty`
    and defaults to "10sp".
    '''

    font_color = ListProperty([1, 1, 1, 1])
    ''' Font color of label.
    :attr:`font_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [1,1,1,1].
    '''

    knobimg_size = BoundedNumericProperty(0.9, max=1.0, min=0.1)
    ''' Internal proportional size of rectangle that holds
    :attr:`knobimg_source` texture.
    :attr:`knobimg_size` is a :class:`~kivy.properties.BoundedNumericProperty`
    and defaults to 0.9.
    '''

    show_marker = BooleanProperty(True)
    ''' Shows/hides marker surrounding knob. use :attr:`knob_size` < 1.0 to
    leave space to marker.
    :attr:`show_marker` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    marker_img = StringProperty("")
    '''Path of texture image that visually represents the knob marker. The
    marker is rendered in a centered Ellipse (Circle) with the same size of
    the widget and goes from angle_start=:attr:`marker_startangle` to
    angle_end=:attr:`_angle`.
    :attr:`marker_img` is a :class:`~kivy.properties.StringProperty` and
    defaults to "".
    '''

    marker_color = ListProperty([1, 1, 1, 1])
    '''Color to apply to :attr:`marker_img` texture when loaded.
    :attr:`marker_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [1,1,1,1].
    '''

    knobimg_bgcolor = ListProperty([0, 0, 0, 1])
    ''' Background color behind :attr:`knobimg_source` texture.
    :attr:`value` is a :class:`~kivy.properties.ListProperty` and defaults
    to [0,0,0,1].
    '''

    markeroff_img = StringProperty("")
    '''Path of texture image that visually represents the knob marker where
    it's off, that is, parts of the marker that haven't been reached yet by
    the knob (:attr:`value`).
    :attr:`markeroff_img` is a :class:`~kivy.properties.StringProperty`
    and defaults to "".
    '''

    markeroff_color = ListProperty([0, 0, 0, 0])
    '''Color applied to :attr:`markeroff_img` int the Canvas.
    :attr:`markeroff_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [0,0,0,0].
    '''

    marker_startangle = NumericProperty(0)
    '''Starting angle of Ellipse where :attr:`marker_img` is rendered.
    :attr:`value` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    marker_ahead = NumericProperty(0)
    ''' Adds degrees to angle_end of marker (except when :attr:`value` == 0).
    :attr:`marker_ahead` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    _angle          = NumericProperty(0)            # Internal angle calculated from value.
    _angle_step     = NumericProperty(0)            # Internal angle_step calculated from step.
    _label          = ObjectProperty(None)          # Internal label that show value.


    def __init__(self, *args, **kwargs):
        super(Knob, self).__init__(*args, **kwargs)
        self.bind(show_label    =   self._show_label)
        self.bind(show_marker   =   self._show_marker)
        self.bind(value         =   self._value)


    def _show_label(self, o, flag):
        if flag and (self._label not in self.children):
            self.add_widget(self._label)
        elif not flag and (self._label in self.children):
            self.remove_widget(self._label)


    def _value(self, o, value):
        self._angle     =   pow( (value - self.min)/(self.max - self.min), 1./self.curve) * 360.
        self.on_knob(value)

    def _show_marker(self, o, value):
        # "show/hide" marker.
        if value:
            self.knobimg_bgcolor[3] = 1
            self.marker_color[3] = 1
            self.markeroff_color[3] = 1
        else:
            self.knobimg_bgcolor[3] = 0
            self.marker_color[3] = 0
            self.markeroff_color[3] = 0


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.update_angle(touch)


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.update_angle(touch)


    def update_angle(self, touch):
        posx, posy          =   touch.pos
        cx, cy              =   self.center
        rx, ry              =   posx - cx, posy - cy

        if ry >= 0:                                 # Quadrants are clockwise.
            quadrant = 1 if rx >= 0 else 4
        else:
            quadrant = 3 if rx <= 0 else 2

        try:
            angle    = math.atan(rx / ry) * (180./math.pi)
            if quadrant == 2 or quadrant == 3:
                angle = 180 + angle
            elif quadrant == 4:
                angle = 360 + angle

        except:                                   # atan not def for angle 90 and 270
            angle = 90 if quadrant <= 2 else 270

        self._angle_step    =   (self.step*360)/(self.max - self.min)
        self._angle         =   self._angle_step
        while self._angle < angle:
            self._angle     =   self._angle + self._angle_step

        relativeValue   =   pow((angle/360.), 1./self.curve)
        self.value      =   (relativeValue * (self.max - self.min)) + self.min


    #TO OVERRIDE
    def on_knob(self, value):
        pass #Knob values listenerr    
    
#FLOAT KNOB POPUP------------------------------------------------------------


class FloatKnobPopup(Popup):
    '''
    see gh_gui.kv
    '''
    __events__ = ('on_ok', 'on_cancel')
    
    picker=ObjectProperty(None)
    
   
    def on_ok(self):
        pass
    
    def on_cancel(self):
        self.dismiss()

