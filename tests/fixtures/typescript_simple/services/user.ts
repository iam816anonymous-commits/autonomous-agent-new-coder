export class UserService {
    getUser(id: string) {
        return { id, name: "Alice" };
    }
}

export function formatUser(user: { id: string; name: string }) {
    return `${user.name} (${user.id})`;
}
