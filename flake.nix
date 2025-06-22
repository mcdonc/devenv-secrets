{
  description = "devenv-secrets";

  inputs = {};

  outputs = { self }:
    {
      plugin = (import ./default.nix);
    };
}
