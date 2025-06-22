from contextlib import contextmanager
import json
import os
import unittest

@contextmanager
def set_env_var(key, value):
    old_value = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old_value is None:
            del os.environ[key]
        else:
            os.environ[key] = old_value

class Fake:
    pass
            
class FakeKeyring:
    errors = Fake()
    errors.InitError = Exception
    def __init__(self, profile=None):
        if profile is None:
            here = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(here, "template.json")) as f:
                profile = f.read()
        self.profile = profile
    
    def get_password(self, name, key):
        if key == "__meta__":
            return json.dumps({"profiles":["profile"]})
        return self.profile

    def set_password(self, ourname, password, profile):
        self.ourname = ourname
        self.password = password
        self.profile = profile
        

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
        keyring.profile = None
        config = self._makeOne(None, keyring)
        self.assertEqual(config.current_profile, "profile")
        self.assertEqual(config.keyring.ourname, "devenv-secrets")
        self.assertEqual(config.keyring.password, "profile")
        with open(self.template_path) as f:
            self.assertEqual(
                config.keyring.profile,
                f.read()
            )

    def test_ctor_withprofile(self):
        keyring = FakeKeyring()
        keyring.profile = None
        config = self._makeOne("profile", keyring)
        self.assertEqual(config.current_profile, "profile")
        self.assertEqual(config.keyring.ourname, "devenv-secrets")
        self.assertEqual(config.keyring.password, "profile")
        with open(self.template_path) as f:
            self.assertEqual(
                config.keyring.profile,
                f.read()
            )

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
    
