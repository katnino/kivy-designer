from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader, TabbedPanelContent
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.bubble import Bubble, BubbleButton
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

Builder.load_string('''
<MenuHeader>
    color: (1, 1, 1, 1) if self.state == 'normal' else (0, 0, 0, 1)
    font_size: '12dp'
    shorten: True
    text_size: self.size
    padding: '2dp', '2dp'
    background_normal: 'atlas://data/images/defaulttheme/action_item'
    background_disabled_normal: 'atlas://data/images/defaulttheme/button_disabled'
    background_down: 'atlas://data/images/defaulttheme/action_item_down'
    background_disabled_down: 'atlas://data/images/defaulttheme/action_item_down'
    Image:
        source: 'atlas://data/images/defaulttheme/tree_closed'
        size: (20, 20) if root.show_arrow else (0,0)
        center_y: root.center_y
        x: (self.parent.right - self.width) if self.parent else 100

<ContextSubMenu>:
    arrow_image: 'atlas://data/images/defaulttheme/tree_closed'
    Image:
        source: root.arrow_image
        size: (20, 20) if root.attached_menu and len(root._list_children) > 0 else (0,0)
        y: self.parent.y + (self.parent.height/2) - (self.height/2)
        x: self.parent.x + (self.parent.width - self.width)

<MenuButton>:
    background_normal: 'atlas://data/images/defaulttheme/action_item'
    background_disabled_normal: 'atlas://data/images/defaulttheme/button_disabled'
    background_down: 'atlas://data/images/defaulttheme/action_item_down'
    background_disabled_down: 'atlas://data/images/defaulttheme/action_item_down'

<ContextMenu>:
    tab_pos:'top_right'
    do_default_tab: False

<MenuBubble>:
    background_image: 'atlas://data/images/defaulttheme/action_item'
''')


class MenuBubble(Bubble):
    '''
    '''
    pass

class MenuHeader(TabbedPanelHeader):
    '''MenuHeader class. To be used as default TabbedHeader.
    '''
    show_arrow = BooleanProperty(False)


class ContextMenuException(Exception):
    '''ContextMenuException class
    '''
    pass

class MenuButton(Button):
    '''MenuButton class. Used as a default menu button. It auto provides
       look and feel for a menu button.
    '''
    pass

class ContextMenu(TabbedPanel):
    '''ContextMenu class. See module documentation for more information.
      :Events:
        `on_select`: data
            Fired when a selection is done, with the data of the selection as
            first argument. Data is what you pass in the :meth:`select` method
            as first argument.
        `on_dismiss`:
            .. versionadded:: 1.8.0

            Fired when the ContextMenu is dismissed either on selection or on
            touching outside the widget.
    '''
    container = ObjectProperty(None)
    '''(internal) The container which will be used to contain Widgets of
       main menu.
       :data:`container` is a :class:`~kivy.properties.ObjectProperty`, default
       to :class:`~kivy.uix.boxlayout.BoxLayout`.
    '''

    main_tab = ObjectProperty(None)
    '''Main Menu Tab of ContextMenu.
       :data:`main_tab` is a :class:`~kivy.properties.ObjectProperty`, default
       to None.
    '''

    bubble_cls = ObjectProperty(MenuBubble)
    '''Bubble Class, whose instance will be used to create 
       container of ContextMenu.
       :data:`bubble_cls` is a :class:`~kivy.properties.ObjectProperty`, default
       to :class:`MenuBubble`.
    '''

    header_cls = ObjectProperty(MenuHeader)
    '''Header Class used to create Tab Header.
       :data:`header_cls` is a :class:`~kivy.properties.ObjectProperty`, default
       to :class:`MenuHeader`.
    '''

    attach_to = ObjectProperty(allownone=True)
    '''(internal) Property that will be set to the widget on which the drop down
       list is attached to.

       The method :meth:`open` will automatically set that property, while
       :meth:`dismiss` will set back to None.       
    '''

    auto_width = BooleanProperty(True)
    '''By default, the width of the ContextMenu will be the same as the width of
       the attached widget. Set to False if you want to provide your own width.
    '''

    dismiss_on_select = BooleanProperty(True)
    '''By default, the ContextMenu will be automatically dismissed when a selection
    have been done. Set to False to prevent the dismiss.

    :data:`dismiss_on_select` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    max_height = NumericProperty(None, allownone=True)
    '''Indicate the maximum height that the dropdown can take. If None, it will
    take the maximum height available, until the top or bottom of the screen
    will be reached.

    :data:`max_height` is a :class:`~kivy.properties.NumericProperty`, default
    to None.
    '''

    __events__ = ('on_select', 'on_dismiss')

    def __init__(self, **kwargs):
        self._win = None
        self.add_tab = super(ContextMenu, self).add_widget
        self.bubble = self.bubble_cls(size_hint=(None, None))
        self.main_box = None
        self.main_tab = self.header_cls(text='Main')
        self.main_tab.content = ScrollView(size_hint=(1,1))
        self.main_tab.content.bind(height=self.on_scroll_height)

        super(ContextMenu, self).__init__(**kwargs)
        self.bubble.add_widget(self)
        self.bind(size=self._reposition)
        self.bubble.bind(on_height=self._bubble_height)
    
    def _bubble_height(self, *args):
        self.height = self.bubble.height

    def open(self, widget):
        '''Open the dropdown list, and attach to a specific widget.
        Depending the position of the widget on the window and the height of the
        dropdown, the placement might be lower or higher off that widget.
        '''
        # ensure we are not already attached
        if self.attach_to is not None:
            self.dismiss()

        # we will attach ourself to the main window, so ensure the widget we are
        # looking for have a window
        self._win = widget.get_parent_window()
        if self._win is None:
            raise ContextMenuException(
                'Cannot open a dropdown list on a hidden widget')

        self.attach_to = widget
        widget.bind(pos=self._reposition, size=self._reposition)

        self.add_tab(self.main_tab)
        self.switch_to(self.main_tab)
        self.main_tab.show_arrow = False

        self._reposition()

        # attach ourself to the main window
        self._win.add_widget(self.bubble)

    def on_select(self, data):
        pass

    def dismiss(self, *largs):
        '''Remove the dropdown widget from the iwndow, and detach itself from
        the attached widget.
        '''
        if self.bubble.parent:
            self.bubble.parent.remove_widget(self.bubble)
        if self.attach_to:
            self.attach_to.unbind(pos=self._reposition, size=self._reposition)
            self.attach_to = None

        self.switch_to(self.main_tab)

        for child in self.tab_list[:]:
            self.remove_widget(child)
        
        self.dispatch('on_dismiss')

    def select(self, data):
        '''Call this method to trigger the `on_select` event, with the `data`
        selection. The `data` can be anything you want.
        '''
        self.dispatch('on_select', data)
        if self.dismiss_on_select:
            self.dismiss()

    def on_dismiss(self):
        pass
    
    def _set_width_to_bubble(self, *args):
        self.width = self.bubble.width

    def _reposition(self, *largs):
        # calculate the coordinate of the attached widget in the window
        # coordinate sysem
        win = self._win
        widget = self.attach_to
        if not widget or not win:
            return

        wx, wy = widget.to_window(*widget.pos)
        wright, wtop = widget.to_window(widget.right, widget.top)

        # set width and x
        if self.auto_width:
            #Calculate minimum required width
            from kivy.metrics import dp
            if len(self.main_box.children) == 1:
                self.bubble.width = max(self.main_tab.parent.parent.width,
                                        self.main_box.children[0].width)
            else:
                self.bubble.width = max(self.main_tab.parent.parent.width,
                                        *([i.width for i in self.main_box.children]))

        Clock.schedule_once(self._set_width_to_bubble, 0.01)
        # ensure the dropdown list doesn't get out on the X axis, with a
        # preference to 0 in case the list is too wide.
        x = wx
        if x + self.bubble.width > win.width:
            x = win.width - self.bubble.width
        if x < 0:
            x = 0
        self.bubble.x = x

        # determine if we display the dropdown upper or lower to the widget
        h_bottom = wy - self.bubble.height
        h_top = win.height - (wtop + self.bubble.height)
        if h_bottom > 0:
            self.bubble.top = wy
            self.bubble.arrow_pos = 'top_mid'
        elif h_top > 0:
            self.bubble.y = wtop
            self.bubble.arrow_pos = 'bottom_mid'
        else:
            # none of both top/bottom have enough place to display the widget at
            # the current size. Take the best side, and fit to it.
            height = max(h_bottom, h_top)
            if height == h_bottom:
                self.bubble.top = wy
                self.bubble.height = wy
                self.bubble.arrow_pos = 'top_mid'
            else:
                self.bubble.y = wtop
                self.bubble.height = win.height - wtop
                self.bubble.arrow_pos = 'bottom_mid'

    def on_touch_down(self, touch):
        if super(ContextMenu, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            return True
        self.dismiss()

    def on_touch_up(self, touch):
        if super(ContextMenu, self).on_touch_up(touch):
            return True
        self.dismiss()

    def add_widget(self, widget, index=0):
        if self.tab_list and widget == self.tab_list[0].content or\
            widget == self._current_tab.content or self.content == widget or\
            self._tab_layout == widget or\
            isinstance(widget, TabbedPanelContent) or\
            isinstance(widget, TabbedPanelHeader):
            super(ContextMenu, self).add_widget(widget, index)
            return            

        if not self.main_box:
            self.main_box = GridLayout(orientation='vertical',
                                       size_hint_y=None,
                                       cols=1)
            self.main_tab.content.add_widget(self.main_box)
            self.main_box.bind(height=self.on_main_box_height)

        self.main_box.add_widget(widget, index)

        if hasattr(widget, 'cont_menu'):
            widget.cont_menu = self

        widget.bind(height=self.on_child_height)
        widget.size_hint_y = None

    def remove_widget(self, widget):
        if self.main_box and widget in self.main_box.children:
            self.main_box.remove_widget(widget)
        else:
            super(ContextMenu, self).remove_widget(widget)

    def on_scroll_height(self, *args):
        if not self.main_box:
            return

        self.main_box.height = max(self.main_box.height,
                                   self.main_tab.content.height)

    def on_main_box_height(self, *args):
        if not self.main_box:
            return

        self.main_box.height = max(self.main_box.height,
                                   self.main_tab.content.height)

        if self.max_height:
            self.bubble.height = min(self.main_box.height + self.tab_height + dp(10), self.max_height)
        else:
            self.bubble.height = self.main_box.height + self.tab_height + dp(10)

    def on_child_height(self, *args):
        height = 0
        for i in self.main_box.children:
            height += i.height
        
        self.main_tab.content.height = height
        self.main_box.height = height

    def add_tab(self, widget, index = 0):
        super(ContextMenu, self).add_widget(widget, index)


class ContextSubMenu(MenuButton):
    '''ContextSubMenu class. To be used to add a sub menu.
    '''

    attached_menu = ObjectProperty(None)
    '''(internal) Menu attached to this sub menu.
    :data:`attached_menu` is a :class:`~kivy.properties.ObjectProperty`,
    default to None.
    '''

    cont_menu = ObjectProperty(None)
    '''(internal) Reference to the main ContextMenu.
    :data:`cont_menu` is a :class:`~kivy.properties.ObjectProperty`,
    default to None.
    '''

    container = ObjectProperty(None)
    '''(internal) The container which will be used to contain Widgets of
       main menu.
       :data:`container` is a :class:`~kivy.properties.ObjectProperty`, default
       to :class:`~kivy.uix.boxlayout.BoxLayout`.
    '''

    show_arrow = BooleanProperty(False)
    '''(internal) To specify whether ">" arrow image should be shown in the
       header or not. If there exists a child menu then arrow image will be 
       shown otherwise not.
       :data:`show_arrow` is a :class:`~kivy.properties.BooleanProperty`, default
       to False
    '''

    def __init__(self, **kwargs):
        super(ContextSubMenu, self).__init__(**kwargs)
        self._list_children = []

    def on_text(self, *args):
        if self.attached_menu:
            self.attached_menu.text = self.text

    def on_attached_menu(self, *args):
        self.attached_menu.text = self.text

    def add_widget(self, widget, index = 0):
        if isinstance(widget, Image):
            Button.add_widget(self, widget, index)
            return

        self._list_children.append((widget, index))
    
    def on_cont_menu(self, *args):
        self._add_widget()

    def _add_widget(self, *args):
        if not self.cont_menu:
            return

        if not self.attached_menu:
            self.attached_menu = self.cont_menu.header_cls(text=self.text)
            self.attached_menu.content = ScrollView(size_hint=(1,1))
            self.attached_menu.content.bind(height=self.on_scroll_height)
            self.container = GridLayout(orientation='vertical',
                                       size_hint_y = None, cols=1)

            self.attached_menu.content.add_widget(self.container)
            self.container.bind(height=self.on_container_height)
        
        for widget, index in self._list_children:
            self.container.add_widget(widget, index)
            widget.cont_menu = self.cont_menu
            widget.bind(height=self.on_child_height)

    def on_scroll_height(self, *args):
        self.container.height = max(self.container.height,
                                    self.attached_menu.content.height)

    def on_container_height(self, *args):
        self.container.height = max(self.container.height,
                                    self.attached_menu.content.height)

    def on_child_height(self, *args):
        height = 0
        for i in self.container.children:
            height += i.height

        self.container.height = height

    def on_release(self, *args):
        if not self.attached_menu or not self._list_children:
            return

        try:
            index = self.cont_menu.tab_list.index(self.attached_menu)
            self.cont_menu.switch_to(self.cont_menu.tab_list[index])
            tab = self.cont_menu.tab_list[index]
            if hasattr(tab, 'show_arrow') and index != 0:
                tab.show_arrow = True
            else:
                tab.show_arrow = False

        except:
            curr_index = self.cont_menu.tab_list.index(self.cont_menu.current_tab)
            for i in range(curr_index - 1, -1, -1):
                self.cont_menu.remove_widget(self.cont_menu.tab_list[i])

            self.cont_menu.add_tab(self.attached_menu)
            self.cont_menu.switch_to(self.cont_menu.tab_list[0])
            if hasattr(self.cont_menu.tab_list[1], 'show_arrow'):
                self.cont_menu.tab_list[1].show_arrow = True
            else:
                self.cont_menu.tab_list[1].show_arrow = False
            
       

        from kivy.clock import Clock
        Clock.schedule_once(self._scroll, 0.1)

    def _scroll(self, dt):
        from kivy.animation import Animation
        self.cont_menu._reposition()
        total_tabs = len(self.cont_menu.tab_list)
        tab_list = self.cont_menu.tab_list
        curr_index = total_tabs - tab_list.index(self.cont_menu.current_tab)
        to_scroll = len(tab_list)/curr_index
        anim = Animation(scroll_x=to_scroll, d=0.75)
        anim.cancel_all(self.cont_menu.current_tab.parent.parent)
        anim.start(self.cont_menu.current_tab.parent.parent)


if __name__=='__main__':
    from kivy.app import App
    
    from kivy.uix.actionbar import ActionItem
    class ActionContext(ContextSubMenu, ActionItem):
        pass

    Builder.load_string('''
#:import ContextMenu contextual.ContextMenu

<ContextMenu>:
<Test>:
    ActionBar:
        pos_hint: {'top':1}
        ActionView:
            use_separator: True
            ActionPrevious:
                title: 'Action Bar'
                with_previous: False
            ActionOverflow:
            ActionButton:
                text: 'Btn0'
                icon: 'atlas://data/images/defaulttheme/audio-volume-high'
            ActionButton:
                text: 'Btn1'
            ActionButton:
                text: 'Btn2'
            ActionButton:
                text: 'Btn3'
            ActionButton:
                text: 'Btn4'
            ActionGroup:
                mode: 'spinner'
                text: 'Group1'
                dropdown_cls: ContextMenu
                ActionButton:
                    text: 'Btn5'
                    height: 30
                    size_hint_y: None
                ActionButton:
                    text: 'Btnddddddd6'
                    height: 30
                    size_hint_y: None
                ActionButton:
                    text: 'Btn7'
                    height: 30
                    size_hint_y: None

                ActionContext:
                    text: 'Item2'
                    size_hint_y: None
                    height: 30
                    ActionButton:
                        text: '2->1'
                        size_hint_y: None
                        height: 30
                    ActionButton:
                        text: '2->2'
                        size_hint_y: None
                        height: 30
                    ActionButton:
                        text: '2->2'
                        size_hint_y: None
                        height: 30
''')

    class CMenu(ContextMenu):
        pass

    class Test(FloatLayout):
        def __init__(self, **kwargs):
            super(Test, self).__init__(**kwargs)
            self.context_menu = CMenu()

        def add_menu(self, obj, *l):
            self.context_menu = CMenu()
            self.context_menu.open(self.children[0])

    class MyApp(App):
        def build(self):
            return Test()


    MyApp().run()