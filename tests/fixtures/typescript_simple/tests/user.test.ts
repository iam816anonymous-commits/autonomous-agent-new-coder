import { UserService } from "../services/user";

test("getUser", () => {
    const service = new UserService();
    expect(service.getUser("1")).toEqual({ id: "1", name: "Alice" });
});
