import type {PackageInfo} from "#/logic/types.ts";
import {Card} from "@mantine/core";

interface Props {
    data?: PackageInfo
}

export function DependencyView({data}: Props) {

    const packages = data?.requires_dist

    return (
        <Card>
            {packages?.map((package_) =>(package_))}
        </Card>
    );
}