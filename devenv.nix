{ pkgs, lib, config, inputs, devenv-secrets, ... }:

{
  imports = [ devenv-secrets.plugin ];

  secrets.enable = true;
  secrets.profile = "testenv";

  enterShell = ''
    [ "$(secrets)" == "testenv" ] || exit 2
  '';

  enterTest = ''
    secretspyexe -m coverage run "$DEVENV_ROOT/test.py"
    secretspyexe -m coverage report -m --include="test.py,secrets.py"
  '';
}
