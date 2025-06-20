import argparse
import json
import keyring
import os
import shlex
import subprocess
import sys
import tempfile

OURNAME = "devenv-secretsenv"

class Config:
    def __init__(self):
        self.current_env = self.get_default_env()
        envdata = self.load(self.current_env)
        if envdata is None:
            template = self.get_template()
            self.save(self.current_env, template)
            envdata = self.load(self.current_env)
        self.envdata = envdata

    def get_password(self, key, default=None):
        try:
            return keyring.get_password(OURNAME, key)
        except keyring.errors.InitError:
            return default

    def set_password(self, env, serialized):
        keyring.set_password(OURNAME, env, serialized)

    def get_changed(self, old, new):
        changed = set({ k: v for k, v in new.items() if old.get(k) != v })
        return changed

    def get_template(self):
        path = os.environ["DEVENV_SECRETSENV_TEMPLATE"]
        with open(path) as f:
            return f.read()

    def edit(self, env):
        if env is None:
            env = self.current_env

        editor = os.environ.get('EDITOR', 'nano')

        old = self.get_password(env)

        template = self.get_template()

        if old is None:
            old = template

        try:
            old_deserialized = json.loads(old)
        except Exception:
            old_deserialized = {}

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
                    self.save(env, new)
                    import traceback; traceback.print_exc()
                    sys.stderr.write(
                        "Could not deserialize new data, re-edit")
                else:
                    self.save(env, new)
                    if env == self.current_env:
                        newenv = None
                    else:
                        newenv = env
                    self.show_activate_changes_tip(newenv)
        finally:
            os.unlink(temp_filename)

    def show_activate_changes_tip(self, newenv=None):
        if newenv:
            newenv = f"  secretsenv switch {newenv} && "
        else:
            newenv="  "
        sys.stderr.write(
            "To activate your changes, run:\n"
            f"\n{newenv}"
            'eval "$(secretsenv export)"\n'
            "\n"
            "Or exit and reenter the devenv shell\n"
        )
        sys.stderr.flush()

    def save(self, env, serialized):
        self.set_password(env, serialized)

    def load(self, env, default=None):
        serialized = self.get_password(env, default)
        try:
            return json.loads(serialized)
        except (json.decoder.JSONDecodeError, TypeError):
            return default

    def get_meta(self):
        meta = self.get_password("__meta__")
        if meta is None:
            meta = json.dumps({"envs": ["dev"]}, indent=4)
            self.set_password("__meta__", meta)
        return meta

    def load_meta(self):
        meta = self.get_meta()
        return json.loads(meta)

    def serialize(self, config):
        serialized = json.dumps(config, indent=4, sort_keys=True)
        return serialized

    def get_default_env(self):
        meta = json.loads(self.get_meta())
        return meta["envs"][0]

    def switch(self, env):
        meta = json.loads(self.get_meta())
        if not env in meta["envs"]:
            raise ValueError(f"no such env named {env}")
        meta["envs"].remove(env)
        meta["envs"].insert(0, env)
        meta = json.dumps(meta, indent=2)
        self.set_password("__meta__", meta)
        self.show_activate_changes_tip()

    def list(self):
        meta = self.load_meta()
        envs = meta["envs"]
        current = envs[0]
        for env in sorted(envs):
            sys.stdout.write(env)
            if env == current:
                print("*")
            else:
                print()

    def delete(self, name):
        meta = self.load_meta()
        envs = meta["envs"]
        current = envs[0]
        if name == current:
            print("Cannot delete current env")
            sys.exit(1)
        if not name in envs:
            print(f"No such env {name}")
            sys.exit(1)
        envs.remove(name)
        meta = json.dumps(meta)
        self.set_password("__meta__", meta)
        keyring.delete_password(OURNAME, name)

    def copy(self, src, target):
        meta = self.load_meta()
        envs = meta["envs"]
        if not src in envs:
            print(f"No such env {src}")
            sys.exit(1)
        current = envs[0]
        if target == current:
            print(f"Cannot copy on top of current env {target}")
            sys.exit(1)
        copied = self.get_password(src)
        if not target in envs:
            envs.append(target)
        self.save(target, copied)
        self.set_password("__meta__", self.serialize({"envs":list(envs)} ))

    def export(self):
        envvars = {
            "DEVENV_SECRETSENV": self.current_env,
        }
        envvars.update(self.envdata)

        for k, v in sorted(envvars.items()):
            quoted = shlex.quote(v)
            print(f"{k}={quoted}")
            print(f"export {k}")

    def run(self, cmd, **kw):
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            **kw
        )

if __name__ == "__main__":
    main_parser = argparse.ArgumentParser(description="secretsenv")
    subparsers= main_parser.add_subparsers(
        dest="command",
        required=False,
        help="No arguments means show current default secretsenv"
    )
    edit_parser = subparsers.add_parser(
        "edit", help="Edit an environment"
    )
    edit_parser.add_argument(
        "name", help="The environment name to edit", default=None, nargs="?"
    )

    switch_parser = subparsers.add_parser(
        "switch", help="Make an environment the default"
    )
    switch_parser.add_argument(
        "name", help="The environment name to switch to"
    )

    list_parser = subparsers.add_parser(
        "list", help="Show all available environments"
    )

    delete_parser = subparsers.add_parser(
        "delete", help="Delete an environment"
    )
    delete_parser.add_argument(
        "name", help="The environment name to delete"
    )

    copy_parser = subparsers.add_parser(
        "copy", help="Copy an environment"
    )
    copy_parser.add_argument(
        "source", help="The source environment name"
    )
    copy_parser.add_argument(
        "target", help="The target environment name"
    )

    export_parser = subparsers.add_parser(
        "export", help="Output shell commands to export the required envvars"
    )

    args = main_parser.parse_args()

    config = Config()

    if not args.command:
        print(config.current_env)

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
