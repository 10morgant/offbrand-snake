import type {PackageInfo} from "#/logic/types.ts";
import {Card, Stack, Text} from "@mantine/core";
import {UserCard} from "#/components /python/package/UserCard.tsx";

interface Props {
    pack?: PackageInfo;
    loading?: boolean
}

export function Overview({pack, loading = false}: Props) {
    const {versions, description, ...rest} = pack?? {}
    return (
        <Stack gap={20} align={"center"} justify={"center"}>
            <UserCard
                name={pack?.author}
                email={pack?.author_email}
                type={"Author"}
            />
            <Card>
                <Stack>
                    <Text>{pack?.license}</Text>
                    <Text>{pack?.provides_extra}</Text>
                </Stack>
            </Card>
            <Card>
                <pre>

                    {JSON.stringify(rest, null, 2)}
                </pre>
            </Card>
        </Stack>
    );
}