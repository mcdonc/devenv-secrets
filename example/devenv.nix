{ pkgs, lib, config, inputs, devenv-secrets, ... }:

{
  imports = [ devenv-secrets.plugin ];

  secrets.enable = true;
  secrets.profile = "example";

  env = {
    EDITOR = "emacs -nw";
  };

}
