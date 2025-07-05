
let
  pkgs = import <nixpkgs> {};
in

pkgs.mkShell rec {

  buildInputs = with pkgs; [
    python310
  ];

  shellHook = ''
    echo "marketface environment enabled"
  '';
}