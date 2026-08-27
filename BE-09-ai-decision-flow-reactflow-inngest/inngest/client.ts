import { Inngest } from "inngest";

/**
 * The Inngest client. Every workflow function in `inngest/` is registered
 * against this client. Run the local dev server with `npm run inngest:dev`
 * and the functions below are auto-discovered and served.
 */
export const inngest = new Inngest({ id: "ticket-router" });
