{ pkgs, lib, config, ... }:

{
  options.secretsenv = {
    enable = lib.mkOption {
      type = lib.types.bool;
      description = "Use secrets";
      default = true;
    };
    env = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      description = "Switch to this env at devenv startup";
      default = null;
    };
  };
  config =
    let
      cfg = config.secretsenv;
      strToBool = str: str != "";
      boolToStr = bool: if bool then "true" else "false";
      # Separate python used by the devenv for keyring-related tasks.
      # Rationale: on Mac, when any of this stuff changes, its Nix store path
      # will change, and the Mac will ask for confirmation to allow the "new"
      # Python access for each password in the keyring.
      #
      # Linux systems need either dbus-python (KDE) or secretstorage (GNOME).
      # but Macs don't.
      #
      # Use python311 to get secretstorage/cryptography to work (fails under
      # 3.12 with "cannot import name 'exceptions' from
      # 'cryptography.hazmat.bindings._rust' (unknown location)" because for
      # whatever reason, the cryptography package has a python-3.11 DLL instead
      # of a python-3.12 one in Nix.
      #
      keyring_python = (
        pkgs.python311.withPackages (python-pkgs: [
          python-pkgs.keyring
          python-pkgs.pyotp
        ] ++ lib.optionals pkgs.stdenv.isLinux [
          python-pkgs.dbus-python
          python-pkgs.secretstorage
        ]
        )
      );
      keyringpyexe = "${keyring_python}/bin/python";
    in
      lib.mkIf cfg.enable {
        scripts.secretsenv.exec = ''
           exec ${keyringpyexe} "${./secretsenv.py}" $@'';
        scripts.keyringpyexe-secretsenv.exec = keyringpyexe;
        env = {
          DEVENV_SECRETSENV_TEMPLATE = ./template.json;
        };

        enterShell = lib.mkAfter ''

          ${
            if
            (cfg.env != null)
            then "secretsenv switch ${cfg.env} 2> /dev/null"
            else ""
          }

          eval "$(secretsenv export)" && \
          echo "secrets envvars set for $(secretsenv)" || \
          echo "Could not export secrets envvars"
        '';
      };
}
