import { test, expect } from "@playwright/test";
test("landing links to the app and customer details support keyboard dismissal", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Explore the app", exact: true }).click();
  await expect(page).toHaveURL(/\/demo$/);
  await page.getByRole("button", { name: /Aisha Rahman/ }).click();
  await expect(page.getByRole("log", { name: "Customer messages" })).toContainText("oat milk");
  if (testInfo.project.name === "mobile") {
    await page.getByRole("button", { name: "All conversations" }).click();
    await expect(page.getByRole("textbox", { name: "Search conversations" })).toBeFocused();
  }
  await page.getByRole("navigation", { name: "Workspace navigation" }).getByRole("link", { name: "Customers", exact: true }).click();
  await page.getByRole("textbox", { name: "Search customers" }).fill("C001");
  const profile = page.getByRole("button", { name: "Aisha Rahman", exact: true });
  await profile.click();
  const dialog = page.getByRole("dialog", { name: "Aisha Rahman" });
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("Oat milk restock notification");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(profile).toBeFocused();
});

test("product screens fit the viewport and sign-in has an accessible password toggle", async ({ page }, testInfo) => {
  for (const route of ["/demo/customers", "/demo/campaign", "/demo/results", "/try", "/login", "/present"]) {
    await page.goto(route);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), route).toBe(true);
    await page.screenshot({ path: `test-results/${route.replaceAll("/", "-").slice(1)}-${testInfo.project.name}.png`, fullPage: true });
  }
  await page.goto("/login");
  const password = page.getByLabel("Password", { exact: true });
  await expect(password).toHaveAttribute("type", "password");
  await page.getByRole("button", { name: "Show password" }).click();
  await expect(password).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Hide password" }).click();
  await expect(password).toHaveAttribute("type", "password");
});

test("landing motion preferences keep the complete story readable", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Reduced motion on" }),
  ).toBeDisabled();
  await expect(page.locator("#how")).toHaveClass(/n-story-static/);
  await expect(page.locator("canvas")).toHaveCount(0);
  const chapters = await page.locator(".n-chapter").evaluateAll((elements) =>
    elements.map((element) => {
      const rect = element.getBoundingClientRect();
      return {
        top: rect.top,
        bottom: rect.bottom,
        left: rect.left,
        right: rect.right,
      };
    }),
  );
  for (let i = 1; i < chapters.length; i++) {
    expect(
      chapters[i].top >= chapters[i - 1].bottom ||
        chapters[i].left >= chapters[i - 1].right,
    ).toBe(true);
  }
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.reload();
  await page.getByRole("button", { name: "Pause 3D motion" }).click();
  await expect(page.locator("#how")).toHaveClass(/n-story-static/);
  await expect(page.locator("canvas")).toHaveCount(0);
  await page.getByRole("button", { name: "Enable 3D motion" }).click();
  await expect(page.locator("#how")).not.toHaveClass(/n-story-static/);
});

test("landing, QR and results show current evidence without overflow", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "A little nudge",
  );
  await expect(page.locator("#evidence")).toContainText("38–85%");
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/landing-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.goto("/present");
  await expect(
    page.getByRole("img", { name: "Open the Nudgely demo chat" }),
  ).toBeVisible();
  await page.goto("/demo/results");
  await expect(
    page.getByRole("heading", { name: "Evidence before promises." }),
  ).toBeVisible();
  await expect(page.locator("main")).toContainText("57%");
});
test("customer filters and reviewed simulation work", async ({
  page,
}, testInfo) => {
  await page.goto("/demo/customers");
  await page.getByRole("textbox", { name: "Search customers" }).fill("C014");
  await expect(page.getByRole("row").filter({ hasText: "C014" })).toContainText(
    "Opted out",
  );
  await page.goto("/demo/campaign");
  const run = page.getByRole("button", { name: "Simulate campaign" });
  await expect(run).toBeDisabled();
  await page.getByRole("checkbox").check();
  await expect(run).toBeEnabled();
  await run.click();
  await expect(page.getByRole("status")).toContainText(
    "9 simulated, 1 held out",
  );
  await expect(run).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Download simulation log" }),
  ).toBeVisible();
  await page.goto("/demo");
  await expect(
    page.getByRole("heading", { name: "A little more personal." }),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/dashboard-${testInfo.project.name}.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
});
test("chat uses a stable session and handles handover and rate limits", async ({
  page,
}) => {
  const bodies: Array<{ session_id: string; text: string }> = [];
  await page.route("**/api/chat", async (route) => {
    bodies.push(route.request().postDataJSON());
    if (bodies.length === 1)
      await route.fulfill({
        json: { reply: null, handover: true, tags: [], customer_id: "WEB001" },
      });
    else
      await route.fulfill({
        status: 429,
        json: {
          error: "This demo has reached its 30-message limit.",
          limited: true,
        },
      });
  });
  await page.goto("/try");
  await page
    .getByRole("textbox", { name: "Message Kampung Fresh" })
    .fill("HUMAN");
  await page.getByRole("textbox", { name: "Message Kampung Fresh" }).press("Enter");
  await expect(page.getByRole("log")).toContainText("recorded for a person");
  await page
    .getByRole("textbox", { name: "Message Kampung Fresh" })
    .fill("Hello again");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.locator(".chat-composer [role=alert]")).toContainText(
    "30-message limit",
  );
  expect(bodies[0].session_id).toBe(bodies[1].session_id);
  await expect(
    page.getByRole("button", { name: "Send message" }),
  ).toBeDisabled();
});
test("signed-out visitors cannot open the live workspace", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
});
