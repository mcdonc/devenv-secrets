{ pkgs, lib, config, inputs, devenv-secretsenv, ... }:

{
  imports = [ devenv-secretsenv.plugin ];

  awsenv.enable = true;

  env = {
    EDITOR = "emacs -nw";
  };

}
