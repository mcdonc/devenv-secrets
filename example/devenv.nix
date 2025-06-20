{ pkgs, lib, config, inputs, devenv-secretsenv, ... }:

{
  imports = [ devenv-secretsenv.plugin ];

  secretsenv.enable = true;
  secretsenv.env = "example";

  env = {
    EDITOR = "emacs -nw";
  };

}
