{
  description = "ADIF Manager - Interactive ADIF file management tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPkgs = pkgs.python3.pkgs;

        src = pkgs.lib.cleanSourceWith {
          src = pkgs.lib.cleanSource ./.;
          filter = name: type:
            let
              baseName = baseNameOf name;
            in
              !(
                # Exclude version control
                baseName == ".git"
                # Exclude virtual environments
                || baseName == ".venv"
                || baseName == "venv"
                # Exclude Python bytecode
                || baseName == "__pycache__"
                || pkgs.lib.hasSuffix ".pyc" name
                || pkgs.lib.hasSuffix ".pyo" name
                # Exclude IDE and editor configs
                || baseName == ".idea"
                || baseName == ".vscode"
                || baseName == ".envrc"
                # Exclude Nix artifacts
                || baseName == "result"
                || pkgs.lib.hasSuffix ".nix" name && baseName != "flake.nix"
              );
        };
      in
      {
        packages.default = pythonPkgs.buildPythonApplication {
          pname = "adif-manage";
          version = "0.2.1";
          inherit src;

          pyproject = true;
          build-system = [ pythonPkgs.hatchling ];

          # Runtime dependencies
          dependencies = [ pythonPkgs.prompt-toolkit ];

          # No optional dependency groups
          optional-dependencies = { };
        };
      }
    );
}
