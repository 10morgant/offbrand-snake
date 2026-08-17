import {Card, Flex, Stack, Text, Title} from "@mantine/core";
import {IconPackage} from "@tabler/icons-react";
import type {PackageInfo} from "#/logic/types.ts";
import {Link} from "@tanstack/react-router";

interface Props {
    data?: PackageInfo
}

export function PackageCard({data}: Props) {
    return (
        <Card
            pt={20} p={10} withBorder shadow={"md"}
            component={Link}
            to={`/project/$pack`}
            // @ts-ignore
            params={{pack: data?.name}}
        >
            <Flex gap={10}>
                <IconPackage/>
                <Title order={4} pb={10}>{data?.name}</Title>
            </Flex>
            <Stack gap={0}>
                <Text c={"dimmed"}>{data?.summary} </Text>
            </Stack>
        </Card>
    );
}