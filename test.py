from contextlib import contextmanager
import json
import os
import unittest

class FakeErrors:
    InitError = Exception

class FakeKeyring:
    errors = FakeErrors()
    def __init__(self):
        self.meta = None
        self.profiles = {}

    def get_password(self, ourname, key):
        import keyring
        if key == "__meta__":
            if self.meta is None:
                raise keyring.errors.InitError
            return self.meta
        profile = self.profiles.get(key)
        if profile is None:
            raise keyring.errors.InitError
        return profile

    def set_password(self, ourname, key, serialized):
        if key == '__meta__':
            self.meta = serialized
        else:
            self.profiles[key] = serialized

class TestConfig(unittest.TestCase):
    def __init__(self, name):
        super().__init__(name)
        here = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(here, "template.json")
        os.environ["DEVENV_SECRETS_TEMPLATE"] = self.template_path

    def _makeOne(self, profile, keyring=None):
        from secrets import Config
        if keyring is None:
            keyring = FakeKeyring()
        config = Config(profile, keyring)
        return config

    def test_ctor_noprofile(self):
        keyring = FakeKeyring()
        config = self._makeOne(None, keyring)
        self.assertEqual(config.current_profile, "dev")
        self.assertEqual(
            json.loads(config.keyring.meta),
            json.loads('{"profiles": ["dev"]}')
        )
        with open(self.template_path) as f:
            self.assertEqual(
                config.keyring.profiles["dev"],
                f.read()
            )

    def test_ctor_withprofile(self):
        keyring = FakeKeyring()
        config = self._makeOne("profile", keyring)
        self.assertEqual(config.current_profile, "profile")
        self.assertEqual(
            json.loads(config.keyring.meta),
            json.loads('{"profiles": ["profile"]}')
        )
        with open(self.template_path) as f:
            self.assertEqual(
                config.keyring.profiles["profile"],
                f.read()
            )

    def test_edit_changes_noerror(self):
        config = self._makeOne("profile")
        new = '{"SECRET1":"a"}'
        def call(cmd):
            fn = cmd[-1]
            with open(fn, "w") as f:
                f.write(new)
        config.call = call
        capture = []
        config.errout = capture.append
        config.edit()
        self.assertEqual(config.keyring.profiles["profile"], new)
        self.assertTrue(capture[0].startswith("To activate"))

    def test_edit_changes_witherror(self):
        config = self._makeOne("profile")
        new = '{"SECRET1":"a}'
        def call(cmd):
            fn = cmd[-1]
            with open(fn, "w") as f:
                f.write(new)
        config.call = call
        capture = []
        config.errout = capture.append
        config.edit()
        self.assertEqual(config.keyring.profiles["profile"], new)
        self.assertTrue(capture[1].startswith("Could not deserialize"))

    def test_edit_nochanges(self):
        config = self._makeOne("profile")
        new = config.keyring.profiles["profile"]
        def call(cmd):
            fn = cmd[-1]
            with open(fn, "w") as f:
                f.write(new)
        config.call = call
        capture = []
        config.errout = capture.append
        config.edit()
        self.assertEqual(config.keyring.profiles["profile"], new)
        self.assertFalse(capture)

    def test_load_cant_deserialize(self):
        config = self._makeOne("profile")
        config.keyring.profiles["profile"] = "{malformed"
        result = config.load("profile", 123)
        self.assertEqual(result, 123)

    def test_export(self):
        config = self._makeOne("profile")
        capture = []
        config.out = capture.append
        config.export()
        actual = '\n'.join(capture)
        expected = '\n'.join([
            "DEVENV_SECRETS_PROFILE=profile",
            "export DEVENV_SECRETS_PROFILE",
            "MYSECRET=secret",
            "export MYSECRET",
            "MYSECRET2=secret2",
            "export MYSECRET2"
        ])
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
