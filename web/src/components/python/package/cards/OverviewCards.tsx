import type {PackageInfo} from "#/logic/types.ts";
import {Card, Flex, Grid, SimpleGrid, Text, Title} from "@mantine/core";
import {UserCard} from "#/components/python/package/cards/UserCard.tsx";
import {IconPackages, IconScale} from "@tabler/icons-react";
import {getLatestVersionNumber} from "#/logic/version.ts";
import {ProvidesExtraCard} from "#/components/python/package/cards/ProvidesExtraCard.tsx";
import {DependenciesCard} from "#/components/python/package/cards/DependenciesCard.tsx";

interface Props {
    data?: PackageInfo
}

export function OverviewCards({data}: Props) {
    const has_extra = (data?.provides_extra.length ?? 0) > 0

    if (has_extra) {
        return (
            <SimpleGrid cols={{base: 1, sm: 2}} spacing="md" pt={30}>
                <Grid gap="md">
                    <Grid.Col w={200}>
                        {(data?.author || data?.author_email) && <UserCard
                            name={data?.author}
                            email={data?.author_email}
                            type={"Author"}
                        />}
                    </Grid.Col>
                    <Grid.Col span={6}>
                        <Card pt={20} p={20} withBorder shadow={"md"}>
                            <Flex gap={10}>
                                <IconScale/>
                                <Title order={4} pb={10}>Licence</Title>
                            </Flex>
                            <Text>{data?.license ?? data?.license_expression}</Text>
                        </Card>
                    </Grid.Col>
                    <Grid.Col span={6}>
                        <Card pt={20} p={20} withBorder shadow={"md"}>
                            <Flex gap={10}>
                                <IconPackages/>
                                <Title order={4} pb={10}>Latest</Title>
                            </Flex>
                            <Text>{getLatestVersionNumber(data?.versions.map((ver) => (ver.version ?? "0.0.0")) ?? [])}</Text>
                        </Card>
                    </Grid.Col>

                    <Grid.Col w={200}>
                        {(data?.requires_dist ?? []).length > 0 && (
                            <DependenciesCard
                                pack={data}
                            />
                        )}
                    </Grid.Col>
                </Grid>
                {has_extra && <ProvidesExtraCard data={data}/>}
            </SimpleGrid>
        );
    }

    return (
        <SimpleGrid cols={{base: 1, sm: 3}} w={1000} spacing="md" pt={30}>
            {(data?.author || data?.author_email) && <UserCard
                name={data?.author}
                email={data?.author_email}
                type={"Author"}
            />}
            <Card pt={20} p={20} withBorder shadow={"md"}>
                <Flex gap={10}>
                    <IconScale/>
                    <Title order={4} pb={10}>Licence</Title>
                </Flex>
                <Text>{data?.license ?? data?.license_expression}</Text>
            </Card>
            <Card pt={20} p={20} withBorder shadow={"md"}>
                <Flex gap={10}>
                    <IconPackages/>
                    <Title order={4} pb={10}>Latest</Title>
                </Flex>
                <Text>{getLatestVersionNumber(data?.versions.map((ver) => (ver.version ?? "0.0.0")) ?? [])}</Text>
            </Card>
        </SimpleGrid>
    );
}