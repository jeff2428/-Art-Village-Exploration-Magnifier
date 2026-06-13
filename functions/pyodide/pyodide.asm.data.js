export async function onRequest(context) {
  return new Response("Not found", { status: 404 });
}
