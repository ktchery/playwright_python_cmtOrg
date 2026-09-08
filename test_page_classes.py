import logging

from playwright.sync_api import expect

from test_utility_basepage import BasePage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Home Page class
class HomePage(BasePage):
    HOME_URL = "https://thecmt.org/"

    def __init__(self, page):
        super().__init__(page)

    def navigate_home(self):
        self.navigate(self.HOME_URL)

    def go_to_auditorium(self):
        self.page.click("xpath=//a[@data-test='template-nav' and contains(text(),'Auditorium')]")
        logging.info("Navigated to Auditorium page")


# Auditorium Page class
class AuditoriumPage(BasePage):
    AUDITORIUM_URL = "https://thecmt.org/auditorium-2"
    VIDEO_ID = "FzW2EzZcJVM"

    # Golden source: the images this gallery is expected to contain, in order.
    GALLERY_IMAGES = [
        "1580823601655-JRS2CVG3WPBIUG8FY6FZ/CMT+HouseLeft.png",
        "1580823609276-Y5H8SMEVJRWJ6Z91ZB57/CMT-1.jpg",
        "1580823608663-GDNGOHPAF96PDT879LCI/CMT-2.jpg",
        "1580823621717-99MTYBPLTYRSTV6GWACT/CMT-3.jpg",
        "1580823615541-CGO8PEY11DRU5J78SNAK/CMT-4.jpg",
        "1580823620204-VY8PDGNGQTUE90ND8YD9/CMT-5.jpg",
        "1580823631675-4FVL7D8FZLBT1PYD49JH/CMT-6.jpg",
        "1580823630688-3E0QV4USL5XXKZWGUK3P/CMT-7.jpg",
        "1580823638406-59SBTHRQ49H4PJ8GB4MS/CMT-8.jpg",
        "1580823651688-CNFT9S1AAYJBIYOQZH14/CMT-9.jpg",
        "1580823660680-AOGALEXVUIXYIGBKCFHR/CMTBalcony.jpg",
        "1580823665857-2MEES7XARVDV4D3GGV5Q/CMT-Gateclose.jpg",
        "1580823669147-1EFTLBE7ZX3FWFDTGFA5/CMT-Gateclose2.jpg",
        "1580823669453-D4LGQOA1WCAP6RBI44L5/CMT-NYSBCornets.jpg",
        "1580823674896-TK2PZV33JH5N1K0MFCKH/cmt-rockband.png",
    ]

    def __init__(self, page):
        super().__init__(page)

    def navigate_auditorium(self):
        self.navigate(self.AUDITORIUM_URL)

    def check_video_playing(self):
        """Verify the Auditorium page embeds the expected video and that it loads."""
        return self.verify_embedded_video(self.VIDEO_ID)

    def check_images_visible(self):
        """Verify the Auditorium gallery contains its expected images, in order."""
        self.verify_gallery_images(self.GALLERY_IMAGES)


# Railton Hall Page class
class RailtonHallPage(BasePage):
    RAILTON_HALL_URL = "https://thecmt.org/railton-hall"
    VIDEO_ID = "FzW2EzZcJVM"

    GALLERY_IMAGES = [
        "1580812436962-WQW4G9LVZKXZD7RN1UXT/Railton+IMG_2905.jpg",
        "1580812462938-G28VB6XMISVZRZ6P3WXA/Railton+IMG_2791.jpg",
        "1580812518357-LLPZZ1TSS204VWX859VF/Railton+IMG_2886-2.jpg",
        "1580812511400-MGUF6LDBXQKT3D1GS9MJ/Railton+IMG_2841.jpg",
    ]

    def __init__(self, page):
        super().__init__(page)

    def navigate_railton_hall(self):
        self.navigate(self.RAILTON_HALL_URL)

    def check_video_playing(self):
        """Verify the Railton Hall page embeds the expected video and that it loads."""
        return self.verify_embedded_video(self.VIDEO_ID)

    def check_images_visible(self):
        """Verify the Railton Hall gallery contains its expected images, in order."""
        self.verify_gallery_images(self.GALLERY_IMAGES)


# Mumford Hall Page class
class MumfordHallPage(BasePage):
    MUMFORD_HALL_URL = "https://thecmt.org/new-index-1"
    VIDEO_ID = "FzW2EzZcJVM"

    GALLERY_IMAGES = [
        "1580811977152-RKF5BQ8BT0UWYS1L8VLV/Mumford+Hall-IMG_3123-3.jpg",
        "1580811980054-B1E3SKQ5UV9GDGWUEJF9/Mumford+Hall+-IMG_3156.jpg",
        "1580812004277-JZT21BW5557412OLFZWQ/Mumford+Hall-IMG_3106-2.jpg",
        "1580811988623-IN6JF6PCKVF1RFVJZJC2/Mumford-bkgd-IMG_5533.jpg",
    ]

    def __init__(self, page):
        super().__init__(page)

    def navigate_mumford_hall(self):
        self.navigate(self.MUMFORD_HALL_URL)
        expect(self.page.locator("//h1[text()='Mumford Hall:']").first).to_have_text(
            "Mumford Hall:", timeout=7000
        )

    def check_video_playing(self):
        """Verify the Mumford Hall page embeds the expected video and that it loads."""
        return self.verify_embedded_video(self.VIDEO_ID)

    def check_images_visible(self):
        """Verify the Mumford Hall gallery contains its expected images, in order."""
        self.verify_gallery_images(self.GALLERY_IMAGES)


# Contact Page class
class ContactPage(BasePage):
    CONTACT_URL = "https://thecmt.org/new-index"
    PHONE_FIELD = "input[autocomplete='tel-national']"
    # Squarespace stamps data-sqsp-button onto the submit control during
    # hydration, after React mounts the form. It is the latest, most reliable
    # marker that the form's handlers are actually bound.
    FORM_READY = "form.react-form-contents button[type='submit'][data-sqsp-button]"

    # Each case blanks or corrupts exactly one field, paired with the validation
    # message the form is expected to show for it.
    INVALID_SUBMISSIONS = [
        ({'fname': '', 'lname': 'tester', 'email': 'wdqwd@yopmail.com',
          'subject': 'Test message', 'message': 'Hello'},
         'First Name is required'),
        ({'fname': 'Test', 'lname': '', 'email': 'qdqwdqwdqw@yopmail.com',
          'subject': 'Test message', 'message': 'Hello'},
         'Last Name is required'),
        ({'fname': 'Test', 'lname': 'tester', 'email': '',
          'subject': 'Test message', 'message': 'Hello'},
         'Email is required.'),
        ({'fname': 'Test', 'lname': 'tester', 'email': 'ewfewfwefew',
          'subject': 'Test message', 'message': 'Hello'},
         'Email is not valid. Email addresses should follow the format user@domain.com'),
        ({'fname': 'Test', 'lname': 'tester', 'email': 'efwefwefwef@yopmail.com',
          'subject': '', 'message': 'Hello'},
         'Subject is required.'),
        ({'fname': 'Test', 'lname': 'tester', 'email': 'wefefwfewef@yopmail.com',
          'subject': 'Test message', 'message': ''},
         'Message is required.'),
    ]

    def __init__(self, page):
        super().__init__(page)

    def reset_form(self):
        """Return to a clean, empty form between submissions.

        The form is rendered by React after the page loads, so no navigation
        event marks it ready: at "domcontentloaded" the <form> does not exist
        yet, and submitting before React binds its handlers silently posts with
        no validation banner. Waiting for form.react-form-contents is the real
        readiness signal. Headed runs masked this via slow_mo, so it only
        surfaced once the suite could run fast.
        """
        self.page.reload(wait_until="domcontentloaded")
        expect(self.page.locator(self.FORM_READY).first).to_be_visible(timeout=15000)
        expect(self.page.locator('//input[@name="fname"]').first).to_be_visible(timeout=15000)

    def navigate_and_verify(self):
        self.navigate(self.CONTACT_URL)
        expect(self.page.locator("//h1[text()='Address: ']").first).to_have_text(
            "Address: ", timeout=7000
        )

    def submit_contact_form(self, fname, lname, email, subject, message, phone=None):
        """Fill and submit the form. Phone is the form's one optional field.

        Note: never fill input[autocomplete='new-password'] — it is a 22px-wide,
        tabindex=-1 spam honeypot, and completing it would get us treated as a bot.
        """
        self.page.fill('//input[@name="fname"]', fname)
        self.page.fill('//input[@name="lname"]', lname)
        self.page.fill('//input[@type="email"]', email)
        self.page.fill('//input[@type="text" and @autocomplete="false"]', subject)
        self.page.fill('//textarea[@aria-invalid="false"]', message)
        if phone is not None:
            self.page.fill(self.PHONE_FIELD, phone)
        self.page.click('//button[@type="submit"]')

    def expect_validation_error(self, message):
        """Assert the form was rejected and shows the given validation message."""
        expect(self.page.locator(
            "//p[contains(text(),'Form submission failed. Review the following information:')]"
        ).first).to_be_visible()
        expect(self.page.locator(f"//p[contains(text(),'{message}')]").first).to_be_visible()
        logging.info(f"Form correctly rejected with: {message}")

    def verify_all_fields_missing_failure(self):
        for message in ['Name is required.', 'Email is required.',
                        'Subject is required.', 'Message is required.']:
            self.expect_validation_error(message)

    def run_negative_scenarios(self):
        """Submit each invalid variation and confirm the matching error appears."""
        # An entirely blank submission should complain about every field at once.
        self.reset_form()
        self.page.click('//button[@type="submit"]')
        self.verify_all_fields_missing_failure()

        for fields, expected_message in self.INVALID_SUBMISSIONS:
            self.reset_form()
            self.submit_contact_form(**fields)
            self.expect_validation_error(expected_message)

    def submit_valid_form(self, fname, lname, email, subject, message, phone=None):
        """Submit a complete, valid form and confirm it is accepted."""
        self.reset_form()
        self.submit_contact_form(fname, lname, email, subject, message, phone)
        expect(self.page.locator("//div[contains(text(),'Thank you!')]").first).to_have_text(
            'Thank you!', timeout=7000
        )
