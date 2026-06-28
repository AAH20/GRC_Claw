class GrcClaw < Formula
  desc "Open-source GRC automation CLI — compliance, evidence, and security graph"
  homepage "https://a2zsoc.com"
  url "https://github.com/AAH20/GRC_Claw/releases/download/v0.8.0/grc-claw-v0.8.0-darwin-arm64.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000" # update on release
  license "MIT"
  version "0.8.0"

  def install
    bin.install "grc-claw" => "grc"
  end

  test do
    system "#{bin}/grc", "--version"
  end
end
