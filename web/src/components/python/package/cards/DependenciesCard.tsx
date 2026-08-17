import {Card, Flex, Skeleton, Stack, Table, Title} from "@mantine/core";
import {IconSearch} from "@tabler/icons-react";
import type {PackageInfo} from "#/logic/types.ts";
import {useQuery} from "@tanstack/react-query";
import {fetchDepsOptions} from "#/logic/queries.ts";
import {Link} from "@tanstack/react-router";

interface Props {
    pack?: PackageInfo
}

export function DependenciesCard({pack}: Props) {
    const {data: deps, isLoading} = useQuery(fetchDepsOptions(pack?.name ?? "-"))

    if (isLoading){
        return <Skeleton />
    }

    if (!deps) {
        return (<></>)
    }

    return (
        <Card pt={20} p={10} withBorder shadow={"md"}>
            <Flex gap={10}>
                <IconSearch/>
                <Title order={4} pb={10}>Dependencies</Title>
            </Flex>
            <Stack gap={0}>
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>Name</Table.Th>
                            <Table.Th>Version</Table.Th>
                            <Table.Th>If</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {deps.map((dep) => (
                            <Table.Tr key={dep.name}>
                                <Table.Td><Link to={"/project/$pack"}
                                                params={{pack: dep.name}}>{dep.name}</Link></Table.Td>
                                <Table.Td>{dep.specifier}</Table.Td>
                                <Table.Td>{dep.marker ? dep.marker.replace("extra == ", "variant: ") : ""}</Table.Td>
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>

            </Stack>
        </Card>
    );
}