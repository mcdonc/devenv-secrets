{ pkgs, lib, config, inputs, devenv-secrets, ... }:

{
  imports = [ devenv-secrets.plugin ];

  secrets.enable = true;
  secrets.profile = "testenv";

  enterTest = ''
    [ "$MYSECRET" == "secret" ] || exit 1
    secretspyexe -m coverage run "$DEVENV_ROOT/test.py"
    secretspyexe -m coverage report -m --include="test.py,secrets.py"
  '';
}
