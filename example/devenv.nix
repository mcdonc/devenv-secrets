{ pkgs, lib, config, inputs, devenv-secrets, ... }:

{
  imports = [ devenv-secrets.plugin ];

  secrets.enable = true;
  secrets.profile = "example";

  enterShell = ''
    echo "We are using the $(secrets) profile."
  '';

}
