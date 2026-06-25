import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { TrustMarketplace } from "./marketplace/TrustMarketplace.js";

describe("TrustMarketplace", () => {
  it("should issue credential", () => {
    const marketplace = new TrustMarketplace();
    const credential = marketplace.issueCredential({
      issuerOrgId: "issuer-1",
      subjectOrgId: "subject-1",
      type: "compliance",
      framework: "iso27001",
      score: 85,
    });
    assert.ok(credential.id);
    assert.equal(credential.score, 85);
  });

  it("should list and purchase credential", () => {
    const marketplace = new TrustMarketplace();
    const credential = marketplace.issueCredential({
      issuerOrgId: "issuer-1",
      subjectOrgId: "subject-1",
      type: "compliance",
      framework: "soc2",
      score: 90,
    });

    const listing = marketplace.listCredential(credential.id, 500);
    assert.ok(listing);
    assert.equal(listing.status, "active");

    const purchase = marketplace.purchaseCredential(listing.id, "buyer-1");
    assert.ok(purchase);
    assert.equal(purchase.buyerOrgId, "buyer-1");
  });

  it("should calculate org trust score", () => {
    const marketplace = new TrustMarketplace();
    marketplace.issueCredential({ issuerOrgId: "i1", subjectOrgId: "org-1", type: "compliance", framework: "iso27001", score: 80 });
    marketplace.issueCredential({ issuerOrgId: "i1", subjectOrgId: "org-1", type: "trust", framework: "soc2", score: 90 });

    const score = marketplace.getOrgTrustScore("org-1");
    assert.equal(score.overallScore, 85);
    assert.equal(score.credentials, 2);
  });

  it("should filter active listings", () => {
    const marketplace = new TrustMarketplace();
    const c1 = marketplace.issueCredential({ issuerOrgId: "i1", subjectOrgId: "s1", type: "compliance", framework: "iso27001", score: 80 });
    const c2 = marketplace.issueCredential({ issuerOrgId: "i1", subjectOrgId: "s1", type: "trust", framework: "soc2", score: 90 });
    marketplace.listCredential(c1.id, 100);
    marketplace.listCredential(c2.id, 200);

    assert.equal(marketplace.getActiveListings().length, 2);
  });
});
