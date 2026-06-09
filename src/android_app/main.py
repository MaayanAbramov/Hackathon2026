from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
import random

# Import the camera and scanning tool
from kivy_garden.zbarcam import ZBarCam

class ScannerApp(App):
    def build(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Track which field we are currently scanning for
        self.current_scan_field = None 

        # --- Row 1 ---
        row1 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        self.field1 = TextInput(hint_text="Scan Field 1", multiline=False)
        btn_scan1 = Button(text="Scan", size_hint_x=0.3)
        btn_scan1.bind(on_press=lambda instance: self.open_scanner(self.field1))
        row1.add_widget(self.field1)
        row1.add_widget(btn_scan1)

        # --- Row 2 ---
        row2 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        self.field2 = TextInput(hint_text="Scan Field 2", multiline=False)
        btn_scan2 = Button(text="Scan", size_hint_x=0.3)
        btn_scan2.bind(on_press=lambda instance: self.open_scanner(self.field2))
        row2.add_widget(self.field2)
        row2.add_widget(btn_scan2)

        # --- Submit Button & Output ---
        btn_submit = Button(text="Submit", size_hint_y=0.3)
        btn_submit.bind(on_press=self.submit_action)
        self.output_label = Label(text="", size_hint_y=0.3)

        self.main_layout.add_widget(row1)
        self.main_layout.add_widget(row2)
        self.main_layout.add_widget(btn_submit)
        self.main_layout.add_widget(self.output_label)

        return self.main_layout

    def open_scanner(self, target_field):
        """Opens a popup containing the camera feed."""
        self.current_scan_field = target_field

        popup_layout = BoxLayout(orientation='vertical')
        
        # Initialize the camera widget
        self.zbarcam = ZBarCam()
        popup_layout.add_widget(self.zbarcam)

        # Cancel button just in case the user changes their mind
        btn_cancel = Button(text="Cancel", size_hint_y=0.2)
        btn_cancel.bind(on_press=self.close_scanner)
        popup_layout.add_widget(btn_cancel)

        # Create and open the popup
        self.scanner_popup = Popup(title="Scanning...", content=popup_layout, size_hint=(0.9, 0.9))
        self.scanner_popup.open()

        # Start a fast clock to check if the camera saw a barcode
        self.scan_event = Clock.schedule_interval(self.check_scan, 0.1)

    def check_scan(self, dt):
        """Fires 10 times a second to check for decoded symbols."""
        if len(self.zbarcam.symbols) > 0:
            # Grab the very first barcode it sees and decode the bytes to a string
            scanned_data = self.zbarcam.symbols[0].data.decode('utf-8')
            
            # Fill the text input with the data
            self.current_scan_field.text = scanned_data
            
            # Close the camera
            self.close_scanner()

    def close_scanner(self, *args):
        """Safely shuts down the camera and popup."""
        if self.scan_event:
            self.scan_event.cancel()
        
        # Force the camera to stop reading to free up hardware memory
        self.zbarcam.ids.xcamera.play = False 
        self.scanner_popup.dismiss()

    def submit_action(self, instance):
        if self.field1.text.strip() and self.field2.text.strip():
            message = random.choice(["Submitted", "Hola Senior"])
            print(message) 
            self.output_label.text = message 
        else:
            self.output_label.text = "Please complete both scans first."

if __name__ == '__main__':
    ScannerApp().run()