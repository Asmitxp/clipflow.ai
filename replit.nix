{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.ffmpeg
    pkgs.nodejs
    pkgs.fontconfig
    pkgs.dejavu_fonts
  ];
}
