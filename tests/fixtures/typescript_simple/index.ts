import { UserService, formatUser } from "./services/user";

const service = new UserService();
const user = service.getUser("123");
console.log(formatUser(user));
