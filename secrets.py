import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile

OURNAME = "devenv-secrets"

class Config:
    def __init__(self, profile, keyring=None):
        self.keyring = keyring
        if profile is None:
            profile = self.get_default_profile()
        self.current_profile = profile
        self.get_meta() # initialize missing
        profiledata = self.load(self.current_profile)
        if profiledata is None:
            template = self.get_template()
            self.save(self.current_profile, template)
            profiledata = self.load(self.current_profile)
        self.profiledata = profiledata

    def get_password(self, key, default=None):
        try:
            return self.keyring.get_password(OURNAME, key)
        except self.keyring.errors.InitError:
            return default

    def set_password(self, profile, serialized):
        self.keyring.set_password(OURNAME, profile, serialized)

    def get_template(self):
        path = os.environ["DEVENV_SECRETS_TEMPLATE"]
        with open(path) as f:
            return f.read()

    def edit(self, profile):
        if profile is None:
            profile = self.current_profile

        editor = os.environ.get('EDITOR', 'nano')

        old = self.get_password(profile)

        template = self.get_template()

        if old is None:
            old = template

        with tempfile.NamedTemporaryFile(
                suffix=".json", mode="w+", delete=False) as tf:
            temp_filename = tf.name
            tf.write(old)
            tf.flush()

        try:
            cmd = shlex.split(editor)
            cmd.append(temp_filename)
            subprocess.call(cmd)
            with open(temp_filename) as f:
                new = f.read()
                try:
                    json.loads(new)
                except Exception:
                    self.save(profile, new)
                    import traceback; traceback.print_exc()
                    self.errout("Could not deserialize new data, re-edit")
                else:
                    self.save(profile, new)
                    if profile == self.current_profile:
                        newprofile = None
                    else:
                        newprofile = profile
                    self.show_activate_changes_tip(newprofile)
        finally:
            os.unlink(temp_filename)

    def show_activate_changes_tip(self, newprofile=None):
        if newprofile:
            newprofile = f"  secrets switch {newprofile} && "
        else:
            newprofile = "  "
        self.errout(
            "To activate your changes, run:\n"
            f"\n{newprofile}"
            'eval "$(secrets export)"\n'
            "\n"
            "Or exit and reenter the devenv shell\n"
        )

    def save(self, profile, serialized):
        self.set_password(profile, serialized)

    def load(self, profile, default=None):
        serialized = self.get_password(profile, default)
        try:
            return json.loads(serialized)
        except (json.decoder.JSONDecodeError, TypeError):
            return default

    def get_meta(self):
        meta = self.get_password("__meta__")
        if meta is None:
            meta = json.dumps({"profiles": [self.current_profile]}, indent=4)
            self.set_password("__meta__", meta)
        return meta

    def load_meta(self):
        meta = self.get_meta()
        return json.loads(meta)

    def serialize(self, data):
        serialized = json.dumps(data, indent=4, sort_keys=True)
        return serialized

    def get_default_profile(self):
        meta = json.loads(self.get_meta())
        return meta["profiles"][0]

    def switch(self, profile):
        meta = json.loads(self.get_meta())
        if not profile in meta["profiles"]:
            template = self.get_template()
            self.save(profile, template)
            meta["profiles"].append(profile)
        meta["profiles"].remove(profile)
        meta["profiles"].insert(0, profile)
        meta = json.dumps(meta, indent=2)
        self.set_password("__meta__", meta)
        self.show_activate_changes_tip()

    def list(self):
        meta = self.load_meta()
        profiles = meta["profiles"]
        current = profiles[0]
        for profile in sorted(profiles):
            self.out(profile)
            if profile == current:
                self.out("*")
            else:
                self.out("")

    def delete(self, name):
        meta = self.load_meta()
        profiles = meta["profiles"]
        current = profiles[0]
        if name == current:
            self.out("Cannot delete current profile")
            sys.exit(1)
        if not name in profiles:
            self.out(f"No such profile {name}")
            sys.exit(1)
        profiles.remove(name)
        meta = json.dumps(meta)
        self.set_password("__meta__", meta)
        self.keyring.delete_password(OURNAME, name)

    def copy(self, src, target):
        meta = self.load_meta()
        profiles = meta["profiles"]
        if not src in profiles:
            self.out(f"No such profile {src}")
            sys.exit(1)
        current = profiles[0]
        if target == current:
            self.out(f"Cannot copy on top of current profile {target}")
            sys.exit(1)
        copied = self.get_password(src)
        if not target in profiles:
            profiles.append(target)
        self.save(target, copied)
        self.set_password(
            "__meta__", self.serialize({"profiles":list(profiles)} )
        )

    def export(self):
        envvars = {
            "DEVENV_SECRETS_PROFILE": self.current_profile,
        }
        envvars.update(self.profiledata)

        for k, v in sorted(envvars.items()):
            quoted = shlex.quote(v)
            self.out(f"{k}={quoted}")
            self.out(f"export {k}")

    def run(self, cmd, **kw):
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            **kw
        )

    def out(self, data):
        print(data)

    def errout(self, data):
        sys.stderr.write(data)
        sys.stderr.flush()

if __name__ == "__main__":
    main_parser = argparse.ArgumentParser(description="secrets")
    subparsers= main_parser.add_subparsers(
        dest="command",
        required=False,
        help="No arguments means show current default profile"
    )
    edit_parser = subparsers.add_parser(
        "edit", help="Edit a profile"
    )
    edit_parser.add_argument(
        "name", help="The profile name to edit", default=None, nargs="?"
    )

    switch_parser = subparsers.add_parser(
        "switch", help="Make a  profile the default"
    )
    switch_parser.add_argument(
        "name", help="The profile name to make the default profile"
    )

    list_parser = subparsers.add_parser(
        "list", help="Show all available profiles"
    )

    delete_parser = subparsers.add_parser(
        "delete", help="Delete a profile"
    )
    delete_parser.add_argument(
        "name", help="The profile name to delete"
    )

    copy_parser = subparsers.add_parser(
        "copy", help="Copy a profile"
    )
    copy_parser.add_argument(
        "source", help="The source profile name"
    )
    copy_parser.add_argument(
        "target", help="The target profile name"
    )

    export_parser = subparsers.add_parser(
        "export", help="Output shell commands to export the required envvars"
    )

    args = main_parser.parse_args()

    profile = os.environ.get("DEVENV_SECRETS_PROFILE")

    try:
        import keyring
    except ImportError:
        keyring = None # for tests

    config = Config(profile, keyring)

    if not args.command:
        config.out(config.current_profile)

    if args.command == "edit":
        config.edit(args.name)

    if args.command == "switch":
        config.switch(args.name)

    if args.command == "list":
        config.list()

    if args.command == "delete":
        config.delete(args.name)

    if args.command == "copy":
        config.copy(args.source, args.target)

    if args.command == "export":
        config.export()
