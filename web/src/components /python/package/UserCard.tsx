import {Avatar, Card, Flex, Stack, Text, Title} from "@mantine/core";

interface Props {
    name?: string | null;
    email?: string | null;
    type?: string | null;
}

export function UserCard({name, email, type}: Props) {
    return (
        <Card radius={0} p={20} withBorder shadow={"md"}>
            <Title order={4} pb={10}>{type}</Title>
            <Flex gap={10} align={"center"}>
                <Avatar name={name ?? ""} color="initials" ></Avatar>
                <Stack gap={0}>
                    <Text>{name ? name : email}</Text>
                    <Text>{name ? email : ""}</Text>
                </Stack>
            </Flex>
        </Card>
    );
}