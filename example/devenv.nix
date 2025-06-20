{ pkgs, lib, config, inputs, devenv-secretsenv, ... }:

{
  imports = [ devenv-secretsenv.plugin ];

  secretsenv.enable = true;

  env = {
    EDITOR = "emacs -nw";
  };

}
