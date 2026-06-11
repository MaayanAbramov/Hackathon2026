from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
import json

from kivy_garden.zbarcam import ZBarCam

# --- Theme Colors (Nano Banana Aesthetic) ---
BG_COLOR = (0.07, 0.07, 0.07, 1)          
CARD_COLOR = (0.12, 0.12, 0.12, 1)        
ACCENT_YELLOW = (1, 0.96, 0.61, 1)        
ACCENT_GREEN = (0.65, 0.84, 0.65, 1)      
TEXT_COLOR = (0.9, 0.9, 0.9, 1)           
DARK_TEXT = (0.1, 0.1, 0.1, 1)            

Window.clearcolor = BG_COLOR

class RoundedCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        with self.canvas.before:
            Color(*CARD_COLOR)
            self.rect = RoundedRectangle(radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ScannerApp(App):
    def build(self):
        Logger.info("ScannerApp: Booting up UI...")
        
        self.SERVER_IP = "132.68.34.90"
        self.SERVER_PORT = "5000"
        
        self.current_scan_field = None 
        self.scan_event = None
        self.routing_path = [] # Stores doctor routing sequence

        self.main_layout = BoxLayout(orientation='vertical', padding=[20, 40, 20, 20], spacing=20)
        
        # --- Header ---
        header = Label(
            text="FindMyPatient ER Triage", font_size='22sp', bold=True, color=ACCENT_YELLOW,
            size_hint_y=None, height=50, halign='center', valign='middle'
        )
        self.main_layout.add_widget(header)

        # ==========================================
        # CARD 1: Patient Identification
        # ==========================================
        self.card_patient = RoundedCard(size_hint_y=None, height=160)
        lbl_patient = Label(text="1. Patient Identification", bold=True, color=TEXT_COLOR, size_hint_y=None, height=40, halign='left', valign='middle')
        lbl_patient.bind(size=lbl_patient.setter('text_size'))
        
        self.row1 = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=50)
        self.field1 = TextInput(hint_text="Patient Barcode ID", multiline=False, size_hint_x=0.7, background_color=(0.2, 0.2, 0.2, 1), foreground_color=TEXT_COLOR)
        
        btn_scan1 = Button(text="Scan ID", size_hint_x=0.3, background_normal='', background_color=ACCENT_YELLOW, color=DARK_TEXT, bold=True)
        btn_scan1.bind(on_press=lambda instance: self.open_scanner(self.field1))
        
        self.row1.add_widget(self.field1)
        self.row1.add_widget(btn_scan1)
        self.card_patient.add_widget(lbl_patient)
        self.card_patient.add_widget(self.row1)

        # ==========================================
        # CARD 2: Clinical & Routing Data
        # ==========================================
        self.card_action = RoundedCard(size_hint_y=None, height=250)
        self.lbl_action = Label(text="2. Clinical & Routing Data", bold=True, color=TEXT_COLOR, size_hint_y=None, height=40, halign='left', valign='middle')
        self.lbl_action.bind(size=self.lbl_action.setter('text_size'))
        
        # Doctor Checkbox Row
        self.doctor_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        self.chk_doctor = CheckBox(size_hint=(None, None), size=(40, 40), color=ACCENT_YELLOW)
        self.chk_doctor.bind(active=self.toggle_doctor_mode)
        lbl_doctor = Label(text="I am a doctor (Create Path)", halign="left", valign="middle", color=TEXT_COLOR)
        lbl_doctor.bind(size=lbl_doctor.setter('text_size'))
        self.doctor_row.add_widget(self.chk_doctor)
        self.doctor_row.add_widget(lbl_doctor)

        # Nurse Layout (Default)
        self.nurse_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=60)
        self.row2 = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=50)
        self.field2 = TextInput(hint_text="Room/Department Barcode", multiline=False, size_hint_x=0.7, background_color=(0.2, 0.2, 0.2, 1), foreground_color=TEXT_COLOR)
        btn_scan2 = Button(text="Scan Room", size_hint_x=0.3, background_normal='', background_color=ACCENT_YELLOW, color=DARK_TEXT, bold=True)
        btn_scan2.bind(on_press=lambda instance: self.open_scanner(self.field2))
        self.row2.add_widget(self.field2)
        self.row2.add_widget(btn_scan2)
        self.nurse_layout.add_widget(self.row2)

        # Doctor Layout
        self.doctor_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=10)
        self.btn_set_routing = Button(text="Edit Routing Path", background_normal='', background_color=ACCENT_YELLOW, color=DARK_TEXT, bold=True, size_hint_y=None, height=50)
        self.btn_set_routing.bind(on_press=self.open_routing_window)
        self.lbl_routing_summary = Label(text="No path set.", color=TEXT_COLOR, size_hint_y=None, height=40)
        self.doctor_layout.add_widget(self.btn_set_routing)
        self.doctor_layout.add_widget(self.lbl_routing_summary)

        # ==========================================
        # CARD 3: System Controls & Submission
        # ==========================================
        self.card_controls = RoundedCard(size_hint_y=1)
        self.remove_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.remove_checkbox = CheckBox(size_hint=(None, None), size=(50, 50), color=ACCENT_YELLOW)
        self.remove_checkbox.bind(active=self.toggle_remove_mode)
        lbl_remove = Label(text="Discharge / Remove Patient", halign="left", valign="middle", color=TEXT_COLOR)
        lbl_remove.bind(size=lbl_remove.setter('text_size'))
        self.remove_row.add_widget(self.remove_checkbox)
        self.remove_row.add_widget(lbl_remove)

        self.btn_submit = Button(text="Submit to Database", size_hint_y=None, height=60, background_normal='', background_color=ACCENT_GREEN, color=DARK_TEXT, bold=True, font_size='18sp')
        self.btn_submit.bind(on_press=self.submit_action)
        self.output_label = Label(text="", color=ACCENT_YELLOW, size_hint_y=1, text_size=(None, None), halign='center', valign='middle')

        self.card_controls.add_widget(self.remove_row)
        self.card_controls.add_widget(self.btn_submit)
        self.card_controls.add_widget(self.output_label)

        self.update_action_card()
        self.update_layout()
        self.setup_scanner_popup()
        
        return self.main_layout

    # --- UI Layout Toggles ---

    def update_action_card(self):
        """Swaps the inputs in Card 2 between Nurse Scan and Doctor Path based on checkbox."""
        self.card_action.clear_widgets()
        self.card_action.add_widget(self.lbl_action)
        self.card_action.add_widget(self.doctor_row)
        if self.chk_doctor.active:
            self.card_action.add_widget(self.doctor_layout)
        else:
            self.card_action.add_widget(self.nurse_layout)

    def toggle_doctor_mode(self, instance, value):
        self.update_action_card()
        if value:
            self.open_routing_window(None)

    def update_layout(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.main_layout.children[-1] if self.main_layout.children else Label(text="FindMyPatient ER Triage", font_size='22sp', bold=True, color=ACCENT_YELLOW, size_hint_y=None, height=50))
        self.main_layout.add_widget(self.card_patient)
        if not self.remove_checkbox.active:
            self.main_layout.add_widget(self.card_action)
        self.main_layout.add_widget(self.card_controls)

    def toggle_remove_mode(self, instance, value):
        self.update_layout()
        if value:
            self.field2.text = ""
            self.btn_submit.text = "Confirm Discharge"
            self.btn_submit.background_color = (0.9, 0.4, 0.4, 1) 
        else:
            self.btn_submit.text = "Submit to Database"
            self.btn_submit.background_color = ACCENT_GREEN

    # --- Doctor Routing Window Logic ---

    def open_routing_window(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        self.steps_container = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.steps_container.bind(minimum_height=self.steps_container.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.steps_container)
        content.add_widget(scroll)
        
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        btn_add = Button(text="+ Add Step", background_normal='', background_color=ACCENT_YELLOW, color=DARK_TEXT, bold=True)
        btn_add.bind(on_press=self.add_routing_step)
        btn_save = Button(text="Save Path", background_normal='', background_color=ACCENT_GREEN, color=DARK_TEXT, bold=True)
        btn_save.bind(on_press=self.save_routing_path)
        
        controls_layout.add_widget(btn_add)
        controls_layout.add_widget(btn_save)
        content.add_widget(controls_layout)
        
        self.routing_popup = Popup(
            title="Configure Routing Path", title_color=ACCENT_YELLOW, separator_color=ACCENT_YELLOW,
            content=content, size_hint=(0.95, 0.8), background_color=(0.1, 0.1, 0.1, 1)
        )
        
        self.steps_container.clear_widgets()
        if not self.routing_path:
            self.add_routing_step()
        else:
            for step in self.routing_path:
                self.add_routing_step(room=step['room'], urgency=step['urgency'])
                
        self.routing_popup.open()

    def add_routing_step(self, instance=None, room="Room 1", urgency="Urgency 1"):
        if len(self.steps_container.children) >= 7:
            return # Max 7 choices
            
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        
        room_spinner = Spinner(text=room, values=[f"Room {i}" for i in range(1, 9)], size_hint_x=0.5, background_color=(0.3, 0.3, 0.3, 1), color=TEXT_COLOR)
        urgency_spinner = Spinner(text=urgency, values=[f"Urgency {i}" for i in range(1, 6)], size_hint_x=0.5, background_color=(0.3, 0.3, 0.3, 1), color=TEXT_COLOR)
        
        row.room_spinner = room_spinner
        row.urgency_spinner = urgency_spinner
        row.add_widget(room_spinner)
        row.add_widget(urgency_spinner)
        
        self.steps_container.add_widget(row)

    def save_routing_path(self, instance):
        self.routing_path = []
        # Reverse iteration because Kivy add_widget puts the newest element at index 0
        for row in reversed(self.steps_container.children):
            self.routing_path.append({
                "room": row.room_spinner.text,
                "urgency": row.urgency_spinner.text
            })
            
        self.routing_popup.dismiss()
        self.lbl_routing_summary.text = f"Path Set: {len(self.routing_path)} Steps Configured."
        self.lbl_routing_summary.color = ACCENT_GREEN

    # --- Scanner Logic ---
    def on_start(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])

    def setup_scanner_popup(self):
        popup_layout = BoxLayout(orientation='vertical')
        self.zbarcam = ZBarCam()
        self.zbarcam.ids.xcamera.play = False 
        popup_layout.add_widget(self.zbarcam)

        btn_cancel = Button(text="Cancel Scan", size_hint_y=0.15, background_normal='', background_color=(0.8, 0.2, 0.2, 1), color=TEXT_COLOR, bold=True)
        btn_cancel.bind(on_press=self.close_scanner)
        popup_layout.add_widget(btn_cancel)

        self.scanner_popup = Popup(title="Scanning Barcode / QR...", title_color=ACCENT_YELLOW, separator_color=ACCENT_YELLOW, content=popup_layout, size_hint=(0.95, 0.95), background_color=(0.1, 0.1, 0.1, 1))

    def open_scanner(self, target_field):
        self.current_scan_field = target_field
        self.zbarcam.symbols.clear()
        self.scanner_popup.open()
        Clock.schedule_once(self._start_camera_hardware, 0.5)

    def _start_camera_hardware(self, dt):
        self.zbarcam.ids.xcamera.play = True
        self.scan_event = Clock.schedule_interval(self.check_scan, 0.1)

    def check_scan(self, dt):
        if len(self.zbarcam.symbols) > 0:
            scanned_data = self.zbarcam.symbols[0].data.decode('utf-8')
            self.current_scan_field.text = scanned_data
            self.close_scanner()

    def close_scanner(self, *args):
        if self.scan_event:
            self.scan_event.cancel()
            self.scan_event = None
        self.scanner_popup.dismiss()
        Clock.schedule_once(self._stop_camera_hardware, 0.3)

    def _stop_camera_hardware(self, dt):
        self.zbarcam.ids.xcamera.play = False

    # --- Database Submission ---
    def submit_action(self, instance):
        patient_number = self.field1.text.strip()
        dept_barcode = self.field2.text.strip()
        
        if patient_number and not patient_number.isnumeric():
            self.output_label.text = f"Patient ID '{patient_number}' invalid. Must be numeric."
            self.output_label.color = (0.9, 0.4, 0.4, 1) 
            return
        
        # REMOVE PATIENT FLOW
        if self.remove_checkbox.active:
            if not patient_number:
                self.output_label.text = "Please scan/enter patient number to remove."
                self.output_label.color = (0.9, 0.4, 0.4, 1)
                return
            
            content = BoxLayout(orientation='vertical', spacing=15, padding=10)
            content.add_widget(Label(text=f"Are you sure you want to discharge Patient {patient_number}?", halign='center'))
            btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
            btn_ok = Button(text="Discharge", background_normal='', background_color=(0.9, 0.4, 0.4, 1))
            btn_cancel = Button(text="Cancel", background_normal='', background_color=(0.5, 0.5, 0.5, 1))
            btn_layout.add_widget(btn_ok)
            btn_layout.add_widget(btn_cancel)
            content.add_widget(btn_layout)

            self.confirm_popup = Popup(title="Confirm Discharge", title_color=(0.9, 0.4, 0.4, 1), separator_color=(0.9, 0.4, 0.4, 1), content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
            btn_cancel.bind(on_press=self.confirm_popup.dismiss)
            btn_ok.bind(on_press=lambda x: self.process_removal(patient_number))
            self.confirm_popup.open()

        # STANDARD SUBMISSION FLOW
        else:
            payload = {"patientNumber": int(patient_number) if patient_number else 0}
            
            if self.chk_doctor.active:
                if not self.routing_path:
                    self.output_label.text = "Please configure a routing path."
                    self.output_label.color = (0.9, 0.4, 0.4, 1)
                    return
                payload["routingPath"] = self.routing_path
                payload["isDoctorFlow"] = True
            else:
                if not dept_barcode:
                    self.output_label.text = "Please scan a Room."
                    self.output_label.color = (0.9, 0.4, 0.4, 1)
                    return
                payload["roombarcode"] = dept_barcode
                payload["isDoctorFlow"] = False
                
            self.output_label.text = "Sending data to server..."
            self.output_label.color = TEXT_COLOR
            
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/api/update_location"
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            
            UrlRequest(url, req_body=json.dumps(payload), req_headers=headers, method='POST',
                       on_success=self.on_upsert_success, on_failure=self.on_request_error, on_error=self.on_request_error)

    def process_removal(self, patient_number):
        self.confirm_popup.dismiss()
        self.output_label.text = "Sending discharge request..."
        self.output_label.color = TEXT_COLOR
        
        payload = {"patientNumber": int(patient_number)}
        url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/api/remove_patient"
        
        UrlRequest(url, req_body=json.dumps(payload), req_headers={'Content-type': 'application/json'}, method='POST',
                   on_success=self.on_remove_success, on_failure=self.on_request_error, on_error=self.on_request_error)

    def on_upsert_success(self, request, result):
        self.output_label.text = "Record successfully updated."
        self.output_label.color = ACCENT_GREEN
        self.field1.text = ""
        self.field2.text = ""
        self.routing_path = []
        self.lbl_routing_summary.text = "No path set."
        self.lbl_routing_summary.color = TEXT_COLOR
        
    def on_remove_success(self, request, result):
        self.output_label.text = "Patient successfully discharged."
        self.output_label.color = ACCENT_GREEN
        self.field1.text = ""

    def on_request_error(self, request, error):
        self.output_label.text = "Connection Error. Check server IP."
        self.output_label.color = (0.9, 0.4, 0.4, 1)

if __name__ == '__main__':
    ScannerApp().run()