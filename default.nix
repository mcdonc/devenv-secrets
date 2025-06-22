{ pkgs, lib, config, ... }:

{
  options.secrets = {
    enable = lib.mkOption {
      type = lib.types.bool;
      description = "Use secrets";
      default = true;
    };
    profile = lib.mkOption {
      type = lib.types.str;
      description = "Use this profile at devenv startup";
      default = "dev";
    };
  };
  config =
    let
      cfg = config.secrets;
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
      secrets_python = (
        pkgs.python311.withPackages (python-pkgs: [
          python-pkgs.keyring
          python-pkgs.pyotp
        ] ++ lib.optionals pkgs.stdenv.isLinux [
          python-pkgs.dbus-python
          python-pkgs.secretstorage
        ]
        )
      );
      secretspyexe = "${secrets_python}/bin/python";
    in
      lib.mkIf cfg.enable {
        scripts.secrets.exec = ''
           exec ${secretspyexe} "${./secrets.py}" $@'';
        scripts.secretspyexe.exec = secretspyexe;
        env = {
          DEVENV_SECRETS_TEMPLATE = ./template.json;
        };

        enterShell = lib.mkAfter ''
          ${
            if
            (cfg.profile != null)
            then "export DEVENV_SECRETS_PROFILE=" + cfg.profile
            else ""
          }
          eval "$(secrets export 2> /dev/null)" && \
          echo "secrets envvars set for $(secrets)" || \
          echo "Could not export secrets envvars"
        '';
      };
}
