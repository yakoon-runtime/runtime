const projectionToContext = new Map();

export function resolveContext(payload) {
    if (payload.context?.context_id) {
        const ctx = payload.context.context_id;
        projectionToContext.set(payload.id, ctx);
        return ctx;
    }

    return projectionToContext.get(payload.id);
}